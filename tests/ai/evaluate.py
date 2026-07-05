"""AI evaluation runner for the knowledge base answer engine.

Scores the curated evaluation dataset (all_test_cases.json) plus
FAQ-derived retrieval checks across all 10 services, then writes
evaluation_results.json next to this script.

Run from the repo root:
    backend/.venv/Scripts/python.exe tests/ai/evaluate.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = THIS_DIR.parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.knowledge_base import (  # noqa: E402
    SERVICE_DIRS,
    answer_with_metadata,
    load_service_knowledge,
    _tokenize,
)

KB_ROOT = THIS_DIR.parents[1] / "tests" / "knowledge_base"
DATASET_PATH = KB_ROOT / "test_cases.json" / "all_test_cases.json"
RESULTS_PATH = THIS_DIR / "evaluation_results.json"

KEYWORD_RECALL_PASS = 0.30


def keyword_recall(expected: str, answer: str) -> float:
    expected_tokens = _tokenize(expected)
    answer_tokens = _tokenize(answer)
    if not expected_tokens:
        return 0.0
    return len(expected_tokens & answer_tokens) / len(expected_tokens)


def evaluate_dataset() -> list[dict]:
    """Score the hand-written eval cases with keyword recall."""
    with DATASET_PATH.open(encoding="utf-8") as handle:
        cases = json.load(handle)

    results = []
    for case in cases:
        answer = answer_with_metadata(case["service_type"], case["query"])
        recall = keyword_recall(case["expected_answer"], answer.answer)
        results.append({
            "kind": "curated",
            "service": case["service_type"],
            "category": case.get("category", "general"),
            "query": case["query"],
            "expected_answer": case["expected_answer"],
            "answer": answer.answer,
            "confidence": answer.confidence,
            "keyword_recall": round(recall, 3),
            "passed": recall >= KEYWORD_RECALL_PASS
        })
    return results


def evaluate_faq_retrieval(per_service: int = 3) -> list[dict]:
    """Ask each service its own FAQ questions; the exact answer must come back."""
    results = []
    for service_id, folder in sorted(SERVICE_DIRS.items()):
        knowledge = load_service_knowledge(service_id)
        for entry in knowledge.get("faq", [])[:per_service]:
            answer = answer_with_metadata(service_id, entry["question"])
            exact = answer.answer.strip() == str(entry["answer"]).strip()
            results.append({
                "kind": "faq_retrieval",
                "service": folder,
                "category": "faq",
                "query": entry["question"],
                "expected_answer": entry["answer"],
                "answer": answer.answer,
                "confidence": answer.confidence,
                "keyword_recall": round(keyword_recall(entry["answer"], answer.answer), 3),
                "passed": exact
            })
    return results


def main() -> None:
    results = evaluate_dataset() + evaluate_faq_retrieval()

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    avg_confidence = sum(r["confidence"] for r in results) / total

    by_service: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        by_service[r["service"]].append(r["passed"])

    summary = {
        "total_cases": total,
        "passed": passed,
        "accuracy": round(passed / total, 3),
        "average_confidence": round(avg_confidence, 3),
        "per_service": {
            service: {
                "cases": len(flags),
                "passed": sum(flags),
                "accuracy": round(sum(flags) / len(flags), 3)
            }
            for service, flags in sorted(by_service.items())
        }
    }

    RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Evaluated {total} cases ({len(evaluate_dataset())} curated + FAQ retrieval checks)")
    print(f"Accuracy: {summary['accuracy']:.1%} ({passed}/{total} passed)")
    print(f"Average confidence: {summary['average_confidence']:.2f}")
    print("\nPer-service accuracy:")
    for service, stats in summary["per_service"].items():
        print(f"  {service:20s} {stats['passed']}/{stats['cases']} ({stats['accuracy']:.0%})")
    print(f"\nDetailed results written to {RESULTS_PATH}")

    failed = [r for r in results if not r["passed"]]
    if failed:
        print(f"\n{len(failed)} failing cases (first 5):")
        for r in failed[:5]:
            print(f"  [{r['service']}] {r['query'][:60]}... recall={r['keyword_recall']}")


if __name__ == "__main__":
    main()
