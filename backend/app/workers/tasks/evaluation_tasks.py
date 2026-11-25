"""
Evaluation Celery Tasks — Asynchronous Job Processing & Real-Time Progress

Dispatched from API when an evaluation is created. Executes evaluations asynchronously,
stores metrics in PostgreSQL, and publishes real-time progress via Redis pub/sub.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.tasks.evaluation_tasks.run_benchmark", bind=True, max_retries=3)
def run_benchmark(self, evaluation_id: str) -> dict:
    """Execute a complete benchmark evaluation asynchronously."""
    logger.info("benchmark_task_starting", evaluation_id=evaluation_id)
    return asyncio.get_event_loop().run_until_complete(
        _run_benchmark_async(evaluation_id)
    )


async def _publish_progress(redis_client, channel: str, message_data: dict) -> None:
    """Publish evaluation progress message to Redis pub/sub channel."""
    try:
        if redis_client:
            if not redis_client._client:
                await redis_client.initialize()
            await redis_client.publish(channel, json.dumps(message_data))
    except Exception as err:
        logger.warning("redis_publish_failed", channel=channel, error=str(err))


async def _run_benchmark_async(evaluation_id: str) -> dict:
    """Async implementation of evaluation execution."""
    from sqlalchemy import select
    from app.core.redis import redis_client
    from app.database.session import async_session_factory
    from app.evaluators.pipeline import EvaluationPipeline
    from app.models.benchmark import Question
    from app.models.evaluation import Evaluation, EvaluationResult
    from app.models.latency import LatencyRecord
    from app.models.metric import Metric
    from app.models.retrieved_chunk import RetrievedChunk

    # Initialize Redis client for worker process
    await redis_client.initialize()

    redis_channel = f"eval:{evaluation_id}"

    async with async_session_factory() as session:
        # Load evaluation
        stmt = select(Evaluation).where(Evaluation.id == uuid.UUID(evaluation_id))
        result = await session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if not evaluation:
            logger.error("evaluation_not_found", evaluation_id=evaluation_id)
            return {"error": "Evaluation not found."}

        evaluation.status = "running"
        evaluation.started_at = datetime.now(timezone.utc)
        await session.commit()

        await _publish_progress(redis_client, redis_channel, {
            "type": "progress",
            "evaluation_id": evaluation_id,
            "status": "running",
            "completed": 0,
            "total": evaluation.total_questions,
            "progress_percent": 0.0,
        })

        # Load questions
        q_stmt = (
            select(Question)
            .where(Question.suite_id == evaluation.suite_id)
            .order_by(Question.order_index)
        )
        q_result = await session.execute(q_stmt)
        questions = q_result.scalars().all()

        config = evaluation.config_snapshot or {}
        concurrency_limit = int(config.get("concurrency", 3))
        question_timeout = float(config.get("question_timeout", 60.0))

        pipeline = EvaluationPipeline(
            chatbot_url=config.get("chatbot_url", "http://localhost:8000/api/v1/demo/chatbot"),
            chatbot_method=config.get("chatbot_method", "POST"),
            enabled_evaluators=evaluation.enabled_evaluators,
            concurrency=concurrency_limit,
        )

        scores_by_type: dict[str, list[float]] = {}
        total_overall_scores: list[float] = []
        completed_counter = 0
        failed_counter = 0
        lock = asyncio.Lock()
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_single_question(idx: int, question: Question):
            nonlocal completed_counter, failed_counter
            async with semaphore:
                eval_status = "success"
                error_msg = None
                eval_data = None
                chatbot_result = {}

                try:
                    # Execute evaluation with timeout
                    eval_data = await asyncio.wait_for(
                        pipeline.evaluate_question(
                            question_text=question.text,
                            expected_answer=question.expected_answer,
                            expected_context=question.expected_context,
                        ),
                        timeout=question_timeout,
                    )
                    chatbot_result = eval_data.get("chatbot_result", {})
                    if not chatbot_result.get("response_text"):
                        eval_status = "failed"
                        error_msg = chatbot_result.get("error") or "Chatbot returned empty response."
                except asyncio.TimeoutError:
                    eval_status = "timeout"
                    error_msg = f"Evaluation timed out after {question_timeout}s."
                except Exception as err:
                    eval_status = "failed"
                    error_msg = str(err)

                async with lock:
                    try:
                        # Store per-question result in PostgreSQL
                        eval_result = EvaluationResult(
                            evaluation_id=evaluation.id,
                            question_id=question.id,
                            response_text=chatbot_result.get("response_text"),
                            response_raw=chatbot_result.get("response_raw"),
                            status=eval_status,
                            error_message=error_msg,
                            overall_score=eval_data.get("overall_score") if eval_data else None,
                        )
                        session.add(eval_result)
                        await session.flush()

                        question_metrics = {}
                        if eval_data and eval_status == "success":
                            for score in eval_data.get("scores", []):
                                metric = Metric(
                                    result_id=eval_result.id,
                                    evaluator_type=score.evaluator_type,
                                    score=score.score,
                                    explanation=score.explanation,
                                    details=score.details,
                                )
                                session.add(metric)
                                scores_by_type.setdefault(score.evaluator_type, []).append(score.score)
                                question_metrics[score.evaluator_type] = score.score

                            if eval_data.get("overall_score") is not None:
                                total_overall_scores.append(eval_data["overall_score"])

                            latency = LatencyRecord(
                                result_id=eval_result.id,
                                total_ms=chatbot_result.get("latency_ms", 0.0),
                            )
                            session.add(latency)

                            for rank, chunk_data in enumerate(chatbot_result.get("retrieved_chunks", [])):
                                chunk = RetrievedChunk(
                                    result_id=eval_result.id,
                                    content=chunk_data.get("content", ""),
                                    source=chunk_data.get("source", ""),
                                    rank=rank,
                                    relevance_score=chunk_data.get("score", 0.0),
                                )
                                session.add(chunk)

                        if eval_status == "success":
                            completed_counter += 1
                        else:
                            failed_counter += 1

                        evaluation.completed_questions = completed_counter + failed_counter
                        evaluation.failed_questions = failed_counter
                        await session.commit()

                        # Publish real-time WebSocket update via Redis
                        progress_pct = round(
                            (evaluation.completed_questions / max(1, len(questions))) * 100, 1
                        )
                        await _publish_progress(redis_client, redis_channel, {
                            "type": "progress",
                            "evaluation_id": evaluation_id,
                            "status": "running",
                            "completed_questions": evaluation.completed_questions,
                            "total_questions": len(questions),
                            "progress": progress_pct,
                            "progress_percent": progress_pct,
                            "current_question": question.text,
                            "latest_metrics": question_metrics,
                        })

                    except Exception as persist_err:
                        logger.error("persist_question_result_failed", error=str(persist_err), qid=str(question.id))

        # Run concurrent batch
        tasks = [process_single_question(i, q) for i, q in enumerate(questions)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Compute aggregated evaluation metrics
        if total_overall_scores:
            evaluation.overall_score = round(sum(total_overall_scores) / len(total_overall_scores), 3)

        if "correctness" in scores_by_type:
            evaluation.accuracy_score = round(sum(scores_by_type["correctness"]) / len(scores_by_type["correctness"]), 3)
        if "hallucination" in scores_by_type:
            evaluation.hallucination_rate = round(sum(scores_by_type["hallucination"]) / len(scores_by_type["hallucination"]), 3)
        if "faithfulness" in scores_by_type:
            evaluation.faithfulness_score = round(sum(scores_by_type["faithfulness"]) / len(scores_by_type["faithfulness"]), 3)
        if "prompt_injection" in scores_by_type:
            evaluation.security_score = round(sum(scores_by_type["prompt_injection"]) / len(scores_by_type["prompt_injection"]), 3)

        evaluation.status = "completed"
        evaluation.completed_at = datetime.now(timezone.utc)
        await session.commit()

        # Final completion WebSocket message
        await _publish_progress(redis_client, redis_channel, {
            "type": "completed",
            "evaluation_id": evaluation_id,
            "status": "completed",
            "overall_score": evaluation.overall_score,
            "total_questions": len(questions),
            "completed_at": evaluation.completed_at.isoformat(),
        })

        logger.info("evaluation_completed", eval_id=evaluation_id, score=evaluation.overall_score)
        return {"evaluation_id": evaluation_id, "status": "completed", "overall_score": evaluation.overall_score}
