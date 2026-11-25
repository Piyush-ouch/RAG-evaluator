"""
RAGBench CLI Importer

Command-line tool to import RAGBench subsets into PostgreSQL.

Usage examples:
    python -m app.benchmark.importer --dataset ragbench --subset finqa --split test --limit 40
    python -m app.benchmark.importer --dataset ragbench --all --limit 40
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.benchmark.ragbench import SUPPORTED_SUBSETS
from app.benchmark.service import RAGBenchImportService
from app.database.session import async_session_factory


async def run_import(
    dataset: str,
    subset: str | None,
    import_all: bool,
    split: str,
    limit: int,
) -> None:
    if dataset.lower() != "ragbench":
        print(f"❌ Error: Dataset '{dataset}' is not supported. Only 'ragbench' is supported.", file=sys.stderr)
        sys.exit(1)

    async with async_session_factory() as session:
        service = RAGBenchImportService(session)

        if import_all or (subset and subset.lower() == "all"):
            print(f"🚀 Starting RAGBench import for all subsets ({', '.join(SUPPORTED_SUBSETS)}) [limit={limit}/subset]...")
            result = await service.import_all_subsets(
                subsets=SUPPORTED_SUBSETS,
                split=split,
                limit_per_subset=limit,
            )
            print("\n📊 Import Summary:")
            print(json.dumps(result, indent=2))
            print(f"\n✅ Successfully completed! Total Inserted: {result['total_inserted']}, Duplicates: {result['total_duplicates']}")

        elif subset:
            sub = subset.lower().strip()
            if sub not in SUPPORTED_SUBSETS:
                print(f"❌ Error: Unknown subset '{sub}'. Supported: {SUPPORTED_SUBSETS}", file=sys.stderr)
                sys.exit(1)

            print(f"🚀 Starting RAGBench import for subset '{sub}' (split='{split}', limit={limit})...")
            result = await service.import_subset(
                subset=sub,
                split=split,
                limit=limit,
            )
            print("\n📊 Import Result:")
            print(json.dumps(result, indent=2))
            print(f"\n✅ Done: Inserted {result['inserted']} questions into '{result['suite_name']}'.")

        else:
            print("❌ Error: Must specify either --subset <name> or --all", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAGBench Dataset Importer for Enterprise RAG Evaluator"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="ragbench",
        help="Target benchmark dataset name (default: ragbench)",
    )
    parser.add_argument(
        "--subset",
        type=str,
        choices=SUPPORTED_SUBSETS + ["all"],
        default=None,
        help="Specific subset to import (finqa, tatqa, pubmedqa, techqa, hotpotqa, all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import all 5 supported RAGBench subsets",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split (default: test)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum questions to import per subset (default: 40)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_import(
                dataset=args.dataset,
                subset=args.subset,
                import_all=args.all,
                split=args.split,
                limit=args.limit,
            )
        )
    except KeyboardInterrupt:
        print("\n⚠️ Import interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
