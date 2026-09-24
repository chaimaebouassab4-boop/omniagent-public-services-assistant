"""Reproducible OmniAgent AI benchmark.

The suite runs the local deterministic retrieval path (no external model or
network dependency), then evaluates the evidence-grounded admin copilot. It
writes the presentation report to docs/ai_evaluation_report.md.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
DATASET_PATH = PROJECT_ROOT / "tests" / "knowledge_base" / "test_cases.json" / "all_test_cases.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "ai_evaluation_report.md"
JSON_RESULTS_PATH = PROJECT_ROOT / "tests" / "ai" / "evaluation_results.json"

sys.path.insert(0, str(BACKEND_DIR))

from app.agents import evaluate_case  # noqa: E402
from app.services.knowledge_base import (  # noqa: E402
    FALLBACK_ANSWER,
    SERVICE_DIRS,
    _tokenize,
    answer_with_metadata,
    load_service_knowledge,
)


CURATED_RECALL_THRESHOLD = 0.18
TARGET_ACCURACY = 0.90


def keyword_recall(expected: str, actual: str) -> float:
    expected_tokens = _tokenize(expected)
    if not expected_tokens:
        return 0.0
    return len(expected_tokens & _tokenize(actual)) / len(expected_tokens)


def evaluate_curated_cases() -> list[dict]:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    results = []
    for index, case in enumerate(cases, 1):
        started = time.perf_counter()
        answer = answer_with_metadata(case["service_type"], case["query"], use_rag=False)
        latency_ms = (time.perf_counter() - started) * 1000
        is_out_of_scope = case["service_type"] == "out_of_scope" or "edge_case" in case.get("category", "")
        recall = keyword_recall(case["expected_answer"], answer.answer)
        if is_out_of_scope:
            passed = answer.confidence < 0.30 and (
                answer.answer == FALLBACK_ANSWER
                or "ما متأكدش" in answer.answer
                or "details" in answer.answer.lower()
            )
        else:
            passed = recall >= CURATED_RECALL_THRESHOLD and answer.confidence >= 0.30
        expected_source = case.get("expected_source", "")
        source_passed = not is_out_of_scope and bool(expected_source) and any(
            expected_source in source for source in answer.sources
        )
        results.append({
            "id": f"curated-{index}",
            "kind": "curated",
            "service": case["service_type"],
            "category": case.get("category", "general"),
            "query": case["query"],
            "expected": case["expected_answer"],
            "actual": answer.answer,
            "confidence": answer.confidence,
            "keyword_recall": round(recall, 3),
            "source_passed": source_passed,
            "latency_ms": round(latency_ms, 3),
            "passed": passed,
            "out_of_scope": is_out_of_scope,
        })
    return results


def evaluate_faq_retrieval(per_service: int = 3) -> list[dict]:
    results = []
    for service_id, folder in sorted(SERVICE_DIRS.items()):
        knowledge = load_service_knowledge(service_id)
        for index, entry in enumerate(knowledge.get("faq", [])[:per_service], 1):
            started = time.perf_counter()
            answer = answer_with_metadata(service_id, str(entry["question"]), use_rag=False)
            latency_ms = (time.perf_counter() - started) * 1000
            expected = str(entry["answer"]).strip()
            exact = answer.answer.strip() == expected
            results.append({
                "id": f"faq-{service_id}-{index}",
                "kind": "faq_retrieval",
                "service": folder,
                "category": "faq",
                "query": entry["question"],
                "expected": expected,
                "actual": answer.answer,
                "confidence": answer.confidence,
                "keyword_recall": round(keyword_recall(expected, answer.answer), 3),
                "source_passed": bool(answer.sources),
                "latency_ms": round(latency_ms, 3),
                "passed": exact,
                "out_of_scope": False,
            })
    return results


def _case(required: list[str], documents: list[tuple[str, str, str]], public_id: int = 9001):
    docs = [
        SimpleNamespace(
            id=f"doc-{index}",
            doc_type=doc_type,
            file_name=f"{doc_type}.pdf",
            validation_status=status,
            ocr_text=ocr,
        )
        for index, (doc_type, status, ocr) in enumerate(documents, 1)
    ]
    return SimpleNamespace(
        public_id=public_id,
        created_at=datetime(2026, 1, 10),
        status="UNDER_REVIEW",
        service_id="evaluation_service",
        service=SimpleNamespace(required_documents=required),
        documents=docs,
    )


def evaluate_copilot() -> list[dict]:
    scenarios = [
        (
            "complete_matching_address",
            _case(
                ["national_id", "proof_of_residence", "address_confirmation"],
                [
                    ("national_id", "verified", "CIN: BK654321\nAdresse: 18 Rue Al Massira, Casablanca"),
                    ("proof_of_residence", "verified", "Adresse: 18 Rue Al Massira, Casablanca"),
                    ("address_confirmation", "verified", "Adresse: 18 Rue Al Massira, Casablanca"),
                ],
            ),
            "APPROVE",
        ),
        (
            "unreadable_identity",
            _case(
                ["national_id", "proof_of_residence", "address_confirmation"],
                [
                    ("national_id", "rejected", "Document illisible - unreadable"),
                    ("proof_of_residence", "verified", "Adresse: 7 Boulevard Zerktouni, Casablanca"),
                    ("address_confirmation", "verified", "Adresse: 7 Boulevard Zerktouni, Casablanca"),
                ],
                9002,
            ),
            "REQUEST_CHANGES",
        ),
        (
            "missing_document",
            _case(
                ["parent_id", "marriage_certificate", "hospital_record"],
                [("parent_id", "verified", "CIN parent"), ("hospital_record", "verified", "Déclaration naissance")],
                9003,
            ),
            "REQUEST_CHANGES",
        ),
        (
            "complete_no_address_requirement",
            _case(
                ["parent_id", "marriage_certificate", "hospital_record"],
                [
                    ("parent_id", "verified", "CIN parent"),
                    ("marriage_certificate", "verified", "Acte mariage"),
                    ("hospital_record", "verified", "Déclaration naissance"),
                ],
                9004,
            ),
            "APPROVE",
        ),
    ]
    results = []
    for name, case, expected in scenarios:
        started = time.perf_counter()
        actual = evaluate_case(case)
        latency_ms = (time.perf_counter() - started) * 1000
        action = actual["recommendation"]["action"]
        grounded = actual["decisionSupportOnly"] and len(actual["documentsCheck"]["items"]) == len(case.service.required_documents)
        results.append({
            "id": f"copilot-{name}",
            "kind": "copilot",
            "service": "admin_copilot",
            "category": name,
            "query": "Compare uploaded evidence with official requirements",
            "expected": expected,
            "actual": action,
            "confidence": 1.0,
            "keyword_recall": 1.0 if action == expected else 0.0,
            "source_passed": grounded,
            "latency_ms": round(latency_ms, 3),
            "passed": action == expected and grounded,
            "out_of_scope": False,
        })
    return results


def build_summary(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(item["passed"] for item in results)
    in_scope = [item for item in results if not item["out_of_scope"] and item["kind"] != "copilot"]
    source_passed = sum(item["source_passed"] for item in in_scope)
    out_of_scope = [item for item in results if item["out_of_scope"]]
    hallucinations = sum(not item["passed"] for item in out_of_scope)
    by_suite: dict[str, list[bool]] = defaultdict(list)
    for item in results:
        by_suite[item["kind"]].append(item["passed"])
    return {
        "total_cases": total,
        "passed": passed,
        "accuracy": passed / total if total else 0.0,
        "source_retrieval_accuracy": source_passed / len(in_scope) if in_scope else 0.0,
        "hallucination_rate": hallucinations / len(out_of_scope) if out_of_scope else 0.0,
        "average_latency_ms": sum(item["latency_ms"] for item in results) / total if total else 0.0,
        "by_suite": {
            suite: {"cases": len(flags), "passed": sum(flags), "accuracy": sum(flags) / len(flags)}
            for suite, flags in sorted(by_suite.items())
        },
    }


def write_report(summary: dict, results: list[dict]) -> None:
    passed_target = summary["accuracy"] > TARGET_ACCURACY
    failures = [item for item in results if not item["passed"]]
    lines = [
        "# OmniAgent AI Evaluation Report",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## Executive result",
        "",
        "| Metric | Target | Measured | Result |",
        "|---|---:|---:|---|",
        f"| Overall accuracy | > 90% | **{summary['accuracy']:.1%}** ({summary['passed']}/{summary['total_cases']}) | {'PASS' if passed_target else 'REVIEW'} |",
        f"| Grounded source retrieval | >= 90% | **{summary['source_retrieval_accuracy']:.1%}** | {'PASS' if summary['source_retrieval_accuracy'] >= .90 else 'REVIEW'} |",
        f"| Out-of-scope hallucination rate | <= 5% | **{summary['hallucination_rate']:.1%}** | {'PASS' if summary['hallucination_rate'] <= .05 else 'REVIEW'} |",
        f"| Average local latency | < 100 ms | **{summary['average_latency_ms']:.2f} ms** | {'PASS' if summary['average_latency_ms'] < 100 else 'REVIEW'} |",
        "",
        "## Scope and methodology",
        "",
        "This benchmark runs entirely against repository data and code. It does not call an external model, network service, or live government registry. The measured system is the deterministic multilingual knowledge-base retriever plus the evidence-grounded civil-servant copilot.",
        "",
        "- Curated suite: keyword recall against 35 hand-written Darija/Arabic public-service cases; the pass threshold is 18% recall with grounded confidence.",
        "- FAQ retrieval suite: exact-answer retrieval for up to three stored FAQs across each of the ten services.",
        "- Copilot suite: four document-review scenarios covering approval, missing evidence, unreadable evidence, and a service where address comparison is not applicable.",
        "- Out-of-scope safety: success requires an uncertainty fallback with confidence below 0.30.",
        "",
        "## Results by suite",
        "",
        "| Suite | Cases | Passed | Accuracy |",
        "|---|---:|---:|---:|",
    ]
    for suite, values in summary["by_suite"].items():
        lines.append(f"| {suite} | {values['cases']} | {values['passed']} | {values['accuracy']:.1%} |")
    lines.extend(["", "## Failed cases", ""])
    if not failures:
        lines.append("No failures in this run.")
    else:
        lines.extend(["| ID | Service | Category | Recall | Actual response |", "|---|---|---|---:|---|"])
        for item in failures:
            actual = str(item["actual"]).replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {item['id']} | {item['service']} | {item['category']} | {item['keyword_recall']:.1%} | {actual} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The result supports a controlled presentation demo, not a claim of legal or production certification. Copilot output is decision support: it refuses approval when required evidence is missing, unreadable, mismatched, or unverifiable. Final responsibility remains with the civil servant.",
        "",
        "## Reproduce",
        "",
        "```powershell",
        r"backend\.venv\Scripts\python.exe tests\evaluate_rag.py",
        "```",
    ])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print("[EVAL] Running deterministic retrieval and copilot benchmark...")
    results = evaluate_curated_cases() + evaluate_faq_retrieval() + evaluate_copilot()
    summary = build_summary(results)
    JSON_RESULTS_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(summary, results)
    print(f"[EVAL] Accuracy: {summary['accuracy']:.1%} ({summary['passed']}/{summary['total_cases']})")
    print(f"[EVAL] Source retrieval: {summary['source_retrieval_accuracy']:.1%}")
    print(f"[EVAL] Hallucination rate: {summary['hallucination_rate']:.1%}")
    print(f"[EVAL] Average latency: {summary['average_latency_ms']:.2f} ms")
    print(f"[EVAL] Report: {REPORT_PATH}")
    return 0 if summary["accuracy"] > TARGET_ACCURACY else 1


if __name__ == "__main__":
    raise SystemExit(main())
