import asyncio
from sqlalchemy import select, delete
from app.database.session import async_session_factory
from app.models.benchmark import BenchmarkSuite, Question
from app.services.benchmark_service import DEFAULT_SUITES

async def main():
    async with async_session_factory() as session:
        for suite_data in DEFAULT_SUITES:
            stmt = select(BenchmarkSuite).where(BenchmarkSuite.name == suite_data["name"])
            res = await session.execute(stmt)
            suite = res.scalar_one_or_none()
            if not suite:
                continue

            print(f"Updating suite '{suite.name}' (current count: {suite.question_count})...")
            
            # Delete existing questions for this default suite
            await session.execute(delete(Question).where(Question.suite_id == suite.id))
            
            # Insert all 10 questions
            for idx, q_data in enumerate(suite_data["questions"]):
                q = Question(
                    suite_id=suite.id,
                    text=q_data["text"],
                    expected_answer=q_data["expected_answer"],
                    category=q_data["category"],
                    difficulty=q_data["difficulty"],
                    order_index=idx,
                    evaluation_type="rag",
                    dataset_version="1.0",
                    is_active=True,
                    tags=["builtin", suite.domain, q_data["category"]],
                )
                session.add(q)

            suite.question_count = len(suite_data["questions"])
            suite.description = suite_data["description"]
            print(f" -> Updated '{suite.name}' with {len(suite_data['questions'])} questions.")

        await session.commit()
        print("✅ Default suites successfully updated to 10 questions each!")

if __name__ == "__main__":
    asyncio.run(main())
