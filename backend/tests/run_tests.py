"""
Test Runner script for verifying Evaluators, Providers, and Pipeline.
"""

import asyncio

from tests.test_evaluators import (
    test_faithfulness_evaluator,
    test_correctness_evaluator,
    test_prompt_injection_checker,
    test_pii_leakage_detector,
    test_role_escalation_evaluator,
)
from tests.test_providers import (
    test_vector_db_factory,
    test_vector_db_factory_unknown,
)


async def main():
    print("=" * 60)
    print("RUNNING RAG EVALUATOR UNIT TESTS")
    print("=" * 60)

    print("[1/7] Testing Faithfulness Evaluator...")
    await test_faithfulness_evaluator()
    print("      [OK] PASSED")

    print("[2/7] Testing Correctness Evaluator...")
    await test_correctness_evaluator()
    print("      [OK] PASSED")

    print("[3/7] Testing Prompt Injection Checker...")
    await test_prompt_injection_checker()
    print("      [OK] PASSED")

    print("[4/7] Testing PII Leakage Detector...")
    await test_pii_leakage_detector()
    print("      [OK] PASSED")

    print("[5/7] Testing Role Escalation Evaluator...")
    await test_role_escalation_evaluator()
    print("      [OK] PASSED")

    print("[6/7] Testing Vector DB Factory...")
    test_vector_db_factory()
    print("      [OK] PASSED")

    print("[7/7] Testing Vector DB Factory Unknown Handling...")
    test_vector_db_factory_unknown()
    print("      [OK] PASSED")

    print("=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! (7/7 PASSED)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
