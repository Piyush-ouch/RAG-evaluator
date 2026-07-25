"""
Evaluation Tasks — Celery Tasks for Running Benchmarks

These tasks are dispatched when a user starts an evaluation.
They run asynchronously, updating progress in real-time.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.tasks.evaluation_tasks.run_benchmark", bind=True, max_retries=3)
def run_benchmark(self, evaluation_id: str) -> dict:
    """
    Execute a complete benchmark evaluation.

    This is the main entry point — dispatched from the API when
    a user starts an evaluation.
    """
    logger.info("benchmark_starting", evaluation_id=evaluation_id)
    return asyncio.get_event_loop().run_until_complete(
        _run_benchmark_async(evaluation_id)
    )


async def _run_benchmark_async(evaluation_id: str) -> dict:
    """Async implementation of benchmark execution."""
    from app.database.session import async_session_factory
    from app.models.evaluation import Evaluation, EvaluationResult
    from app.models.benchmark import Question
    from app.models.metric import Metric
    from app.models.retrieved_chunk import RetrievedChunk
    from app.models.latency import LatencyRecord
    from app.evaluators.pipeline import EvaluationPipeline
    from sqlalchemy import select

    async with async_session_factory() as session:
        # Load evaluation
        stmt = select(Evaluation).where(Evaluation.id == uuid.UUID(evaluation_id))
        result = await session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if not evaluation:
            logger.error("evaluation_not_found", evaluation_id=evaluation_id)
            return {"error": "Evaluation not found."}

        # Update status
        evaluation.status = "running"
        evaluation.started_at = datetime.now(timezone.utc)
        await session.commit()

        # Load questions
        q_stmt = select(Question).where(Question.suite_id == evaluation.suite_id).order_by(Question.order_index)
        q_result = await session.execute(q_stmt)
        questions = q_result.scalars().all()

        # Create pipeline
        pipeline = EvaluationPipeline(
            chatbot_url=evaluation.config_snapshot.get("chatbot_url", ""),
            chatbot_method=evaluation.config_snapshot.get("chatbot_method", "POST"),
            enabled_evaluators=evaluation.enabled_evaluators,
        )

        # Process questions
        total_scores = []
        for i, question in enumerate(questions):
            try:
                result_data = await pipeline.evaluate_question(
                    question_text=question.text,
                    expected_answer=question.expected_answer,
                    expected_context=question.expected_context,
                )

                chatbot_result = result_data["chatbot_result"]

                # Store result
                eval_result = EvaluationResult(
                    evaluation_id=evaluation.id,
                    question_id=question.id,
                    response_text=chatbot_result.get("response_text"),
                    response_raw=chatbot_result.get("response_raw"),
                    status="completed" if chatbot_result.get("response_text") else "failed",
                    error_message=chatbot_result.get("error"),
                    overall_score=result_data.get("overall_score"),
                )
                session.add(eval_result)
                await session.flush()

                # Store metrics
                for score in result_data.get("scores", []):
                    metric = Metric(
                        result_id=eval_result.id,
                        evaluator_type=score.evaluator_type,
                        score=score.score,
                        explanation=score.explanation,
                        details=score.details,
                    )
                    session.add(metric)

                # Store latency
                latency = LatencyRecord(
                    result_id=eval_result.id,
                    total_ms=chatbot_result.get("latency_ms", 0),
                )
                session.add(latency)

                # Store chunks
                for j, chunk_data in enumerate(chatbot_result.get("retrieved_chunks", [])):
                    chunk = RetrievedChunk(
                        result_id=eval_result.id,
                        content=chunk_data.get("content", ""),
                        source=chunk_data.get("source"),
                        rank=j,
                        relevance_score=chunk_data.get("score"),
                    )
                    session.add(chunk)

                if result_data.get("overall_score") is not None:
                    total_scores.append(result_data["overall_score"])

                evaluation.completed_questions = i + 1

            except Exception as e:
                logger.error("question_evaluation_failed", error=str(e), question_id=str(question.id))
                evaluation.failed_questions += 1
                eval_result = EvaluationResult(
                    evaluation_id=evaluation.id,
                    question_id=question.id,
                    status="failed",
                    error_message=str(e),
                )
                session.add(eval_result)
                evaluation.completed_questions = i + 1

            # Commit progress periodically
            if (i + 1) % 10 == 0:
                await session.commit()

        # Compute aggregated metrics
        if total_scores:
            evaluation.overall_score = sum(total_scores) / len(total_scores)

        evaluation.status = "completed"
        evaluation.completed_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            "benchmark_completed",
            evaluation_id=evaluation_id,
            questions=len(questions),
            overall_score=evaluation.overall_score,
        )

        return {
            "evaluation_id": evaluation_id,
            "status": "completed",
            "total_questions": len(questions),
            "overall_score": evaluation.overall_score,
        }
