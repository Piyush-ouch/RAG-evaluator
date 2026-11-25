import asyncio
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.benchmark import BenchmarkSuite

async def main():
    async with async_session_factory() as session:
        res = await session.execute(select(BenchmarkSuite).order_by(BenchmarkSuite.created_at.desc()))
        suites = res.scalars().all()
        print(f"Total Suites: {len(suites)}")
        for s in suites:
            print(f"- Name: {s.name} | Questions: {s.question_count} | Domain: {s.domain} | Source: {s.source_dataset}")

if __name__ == "__main__":
    asyncio.run(main())
