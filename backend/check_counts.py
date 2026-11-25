import asyncio
from sqlalchemy import select, func
from app.database.session import async_session_factory
from app.models.benchmark import BenchmarkSuite, Question
from app.models.evaluation import Evaluation, EvaluationResult

async def check():
    async with async_session_factory() as session:
        suite_cnt = (await session.execute(select(func.count()).select_from(BenchmarkSuite))).scalar()
        question_cnt = (await session.execute(select(func.count()).select_from(Question))).scalar()
        eval_cnt = (await session.execute(select(func.count()).select_from(Evaluation))).scalar()
        result_cnt = (await session.execute(select(func.count()).select_from(EvaluationResult))).scalar()

        print(f"=== DATABASE METRICS SUMMARY ===")
        print(f"Total Benchmark Suites: {suite_cnt}")
        print(f"Total Pre-configured Questions: {question_cnt}")
        print(f"Total Evaluation Runs Triggered: {eval_cnt}")
        print(f"Total Questions Evaluated Across All Runs: {result_cnt}")

if __name__ == "__main__":
    asyncio.run(check())
