"""
Comprehensive Verification Test for RAGBench Integration
Tests:
- API endpoint GET /api/v1/benchmarks
- API endpoint GET /api/v1/benchmarks/{suite_id}/questions
- API endpoint POST /api/v1/benchmarks/import
- API endpoint POST /api/v1/evaluations/quick-start
- Database integrity: question counts, source metadata, expected_context
"""

import sys
import urllib.request
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    print("🧪 1. Testing GET /api/v1/benchmarks/ ...")
    req = urllib.request.Request(f"{BASE_URL}/benchmarks/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        suites = json.loads(resp.read().decode("utf-8"))
    
    print(f"   Found {len(suites)} suites:")
    ragbench_suites = [s for s in suites if s.get("source_dataset") == "ragbench"]
    for s in suites:
        print(f"   - {s['name']}: {s['question_count']} questions (domain: {s['domain']}, source: {s.get('source_dataset')})")
    
    assert len(ragbench_suites) >= 5, f"Expected at least 5 RAGBench suites, found {len(ragbench_suites)}"
    
    total_ragbench_qs = sum(s["question_count"] for s in ragbench_suites)
    print(f"   Total RAGBench questions in DB: {total_ragbench_qs}")
    assert total_ragbench_qs == 200, f"Expected 200 RAGBench questions, got {total_ragbench_qs}"

    print("\n🧪 2. Testing GET /api/v1/benchmarks/{suite_id}/questions ...")
    first_suite = ragbench_suites[0]
    suite_id = first_suite["id"]
    req = urllib.request.Request(f"{BASE_URL}/benchmarks/{suite_id}/questions?limit=5")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        questions = json.loads(resp.read().decode("utf-8"))
    
    print(f"   Fetched {len(questions)} questions from {first_suite['name']}:")
    for q in questions[:2]:
        print(f"   - Q: {q['text'][:60]}...")
        print(f"     Answer: {q.get('expected_answer', '')[:60]}...")
        print(f"     Source ID: {q.get('source_question_id')}, Subset: {q.get('source_subset')}")
        print(f"     Expected Contexts: {len(q.get('expected_context') or [])}")
        assert q.get("source_dataset") == "ragbench"
        assert q.get("source_question_id") is not None
        assert q.get("expected_context") is not None

    print("\n🧪 3. Testing POST /api/v1/benchmarks/import (Idempotent API) ...")
    payload = json.dumps({
        "dataset": "ragbench",
        "subsets": ["finqa"],
        "split": "test",
        "limit_per_subset": 40
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/benchmarks/import",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201, f"Expected 201, got {resp.status}"
        import_res = json.loads(resp.read().decode("utf-8"))
        print(f"   Import API response: inserted={import_res.get('total_inserted')}, duplicates={import_res.get('total_duplicates')}")
        assert import_res.get("total_inserted") == 0, "Expected 0 inserted on duplicate import"
        assert import_res.get("total_duplicates") == 40, "Expected 40 duplicates on re-import"

    print("\n🧪 4. Testing POST /api/v1/evaluations/quick-start with RAGBench suite_id ...")
    eval_payload = json.dumps({
        "chatbot_url": "http://localhost:8000/api/v1/demo/chatbot",
        "suite_id": suite_id,
        "enabled_evaluators": ["correctness", "faithfulness", "hallucination"]
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/evaluations/quick-start",
        data=eval_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 202, f"Expected 202, got {resp.status}"
        eval_res = json.loads(resp.read().decode("utf-8"))
        print(f"   Evaluation launched successfully! ID: {eval_res.get('evaluation_id')}, status: {eval_res.get('status')}")
        assert eval_res.get("status") in ["pending", "running"]

    print("\n🎉 ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    test_api()
