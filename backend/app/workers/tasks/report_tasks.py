"""
Report & Data Processing Tasks
"""

from __future__ import annotations

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.tasks.report_tasks.generate_report_task")
def generate_report_task(evaluation_id: str, report_type: str, format: str, org_id: str) -> dict:
    """Generate a report for an evaluation."""
    logger.info("report_generation_starting", evaluation_id=evaluation_id, type=report_type)
    # Report generation logic will be implemented in the reports module
    return {"status": "completed", "evaluation_id": evaluation_id}


@celery_app.task(name="app.workers.tasks.data_tasks.process_dataset_upload")
def process_dataset_upload(suite_id: str, file_content: str, file_extension: str, org_id: str) -> dict:
    """Process an uploaded dataset file (CSV/JSON/Excel)."""
    logger.info("dataset_processing_starting", suite_id=suite_id, ext=file_extension)
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _process_dataset_async(suite_id, file_content, file_extension, org_id)
    )


async def _process_dataset_async(suite_id: str, file_content: str, file_extension: str, org_id: str) -> dict:
    """Parse and import dataset questions."""
    import io
    import json
    import uuid
    import pandas as pd
    from app.database.session import async_session_factory
    from app.models.benchmark import BenchmarkSuite, Question
    from sqlalchemy import select

    questions_data = []

    if file_extension == "json":
        data = json.loads(file_content)
        if isinstance(data, list):
            questions_data = data
        elif isinstance(data, dict) and "questions" in data:
            questions_data = data["questions"]

    elif file_extension == "csv":
        df = pd.read_csv(io.StringIO(file_content))
        questions_data = df.to_dict(orient="records")

    elif file_extension == "xlsx":
        content_bytes = bytes.fromhex(file_content)
        df = pd.read_excel(io.BytesIO(content_bytes))
        questions_data = df.to_dict(orient="records")

    async with async_session_factory() as session:
        stmt = select(BenchmarkSuite).where(BenchmarkSuite.id == uuid.UUID(suite_id))
        result = await session.execute(stmt)
        suite = result.scalar_one_or_none()
        if not suite:
            return {"error": "Suite not found."}

        count = 0
        for i, qd in enumerate(questions_data):
            question = Question(
                suite_id=uuid.UUID(suite_id),
                text=str(qd.get("question", qd.get("text", ""))),
                expected_answer=str(qd.get("expected_answer", qd.get("answer", ""))) or None,
                category=str(qd.get("category", "")) or None,
                difficulty=str(qd.get("difficulty", "medium")),
                order_index=suite.question_count + i,
                tags=qd.get("tags", []) if isinstance(qd.get("tags"), list) else [],
            )
            session.add(question)
            count += 1

        suite.question_count += count
        await session.commit()

    logger.info("dataset_imported", suite_id=suite_id, questions=count)
    return {"status": "completed", "questions_imported": count}


@celery_app.task(name="app.workers.tasks.maintenance_tasks.cleanup_expired")
def cleanup_expired() -> dict:
    """Periodic cleanup of expired data."""
    logger.info("cleanup_running")
    return {"status": "completed"}
