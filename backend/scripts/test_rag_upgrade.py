"""RAG Upgrade Verification — 10 Query Test Suite.

Tests hybrid search (Vector + BM25), query rewriting (Darija→MSA),
expanded service detection, and direct-answer prompting.

Usage:
    cd backend
    .\.venv\Scripts\python.exe scripts/test_rag_upgrade.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend is on the import path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.rag_service import (
    query_rag,
    _detect_service_from_query,
    _detect_language,
)

# ─── Test Suite ──────────────────────────────────────────────────────────────
TEST_QUERIES = [
    {
        "id": 1,
        "query": "كم الأجل للتصريح بالوفاة؟",
        "lang": "arabic",
        "expected_service": "death_certificate",
        "expected_keywords": ["30"],
        "description": "Standard Arabic — death declaration deadline",
    },
    {
        "id": 2,
        "query": "شنو هي المدة القانونية باش نيلغ على الوفاة؟",
        "lang": "darija",
        "expected_service": "death_certificate",
        "expected_keywords": ["30"],
        "description": "Darija slang — same question about death deadline",
    },
    {
        "id": 3,
        "query": "Quel est le délai final pour déclarer le décès ?",
        "lang": "french",
        "expected_service": "death_certificate",
        "expected_keywords": ["30"],
        "description": "French — death declaration deadline",
    },
    {
        "id": 4,
        "query": "شحال ديال الوقت باش يخرج السجل العدلي؟",
        "lang": "darija",
        "expected_service": "criminal_record",
        "expected_keywords": ["24", "48"],
        "description": "Darija — criminal record processing time",
    },
    {
        "id": 5,
        "query": "شنو الوثائق باش نخرج عقد الازدياد؟",
        "lang": "darija",
        "expected_service": "birth_certificate",
        "expected_keywords": ["البطاقة", "CIN", "CNIE", "الوطنية"],
        "description": "Darija — birth certificate required documents",
    },
    {
        "id": 6,
        "query": "كم رسوم السجل العدلي؟",
        "lang": "arabic",
        "expected_service": "criminal_record",
        "expected_keywords": ["10", "دراهم"],
        "description": "Arabic — criminal record fees",
    },
    {
        "id": 7,
        "query": "واش نقدر نطلب شهادة السكنى أونلاين؟",
        "lang": "darija",
        "expected_service": "residence_certificate",
        "expected_keywords": [],  # any answer about residence is OK
        "description": "Darija — residence certificate online availability",
    },
    {
        "id": 8,
        "query": "Quels sont les documents pour le casier judiciaire ?",
        "lang": "french",
        "expected_service": "criminal_record",
        "expected_keywords": ["CIN", "CNIE", "البطاقة", "carte"],
        "description": "French — criminal record required documents",
    },
    {
        "id": 9,
        "query": "فين نروح باش ناخد شهادة الوفاة؟",
        "lang": "darija",
        "expected_service": "death_certificate",
        "expected_keywords": ["الحالة المدنية", "مكتب", "البلدية"],
        "description": "Darija — where to get death certificate",
    },
    {
        "id": 10,
        "query": "شحال كتكلف شهادة العزوبة؟",
        "lang": "darija",
        "expected_service": "single_status_certificate",
        "expected_keywords": [],  # any answer about fees is OK
        "description": "Darija — single status certificate cost",
    },
]


def _check_keywords(answer: str, keywords: list[str]) -> bool:
    """Check if at least one expected keyword appears in the answer."""
    if not keywords:
        return True  # No keyword requirement → pass
    return any(kw in answer for kw in keywords)


def run_tests() -> None:
    """Execute all 10 test queries and print a results table."""
    print()
    print("=" * 80)
    print("  RAG UPGRADE TEST SUITE — 10 Queries (Hybrid + Rewrite)")
    print("=" * 80)

    total = len(TEST_QUERIES)
    service_pass = 0
    answer_pass = 0
    results = []

    for test in TEST_QUERIES:
        print(f"\n{'─' * 70}")
        print(f"  Test #{test['id']}: {test['description']}")
        print(f"  Query: {test['query']}")
        print(f"{'─' * 70}")

        # ── Service Detection ──
        detected_service = _detect_service_from_query(test["query"])
        svc_ok = detected_service == test["expected_service"]
        if svc_ok:
            service_pass += 1

        # ── Language Detection ──
        detected_lang = _detect_language(test["query"])
        lang_ok = detected_lang == test["lang"]

        # ── RAG Query ──
        t0 = time.time()
        try:
            result = query_rag(
                user_query=test["query"],
                service_type=detected_service,
            )
        except Exception as e:
            result = {"answer": f"ERROR: {e}", "confidence": 0.0, "sources": []}
        elapsed = time.time() - t0

        answer = result.get("answer", "")
        confidence = result.get("confidence", 0.0)
        sources = result.get("sources", [])
        fallback = result.get("fallback_reason")

        kw_ok = _check_keywords(answer, test["expected_keywords"])
        if kw_ok:
            answer_pass += 1

        overall_ok = svc_ok and kw_ok
        status = "✅ PASS" if overall_ok else "❌ FAIL"

        print(f"  Service: {detected_service or 'None'} "
              f"{'✓' if svc_ok else '✗ expected: ' + test['expected_service']}")
        print(f"  Language: {detected_lang} "
              f"{'✓' if lang_ok else '✗ expected: ' + test['lang']}")
        print(f"  Confidence: {confidence}")
        print(f"  Sources: {sources}")
        print(f"  Time: {elapsed:.2f}s")
        if fallback:
            print(f"  ⚠ Fallback: {fallback}")
        print(f"  Answer: {answer[:200]}...")
        if not kw_ok and test["expected_keywords"]:
            print(f"  ⚠ Missing keywords: {test['expected_keywords']}")
        print(f"  → {status}")

        results.append({
            "id": test["id"],
            "status": overall_ok,
            "service_ok": svc_ok,
            "answer_ok": kw_ok,
            "confidence": confidence,
            "elapsed": elapsed,
        })

    # ── Summary ──
    print(f"\n{'=' * 80}")
    print("  SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Service Detection: {service_pass}/{total}")
    print(f"  Answer Quality:    {answer_pass}/{total}")
    overall = sum(1 for r in results if r["status"])
    print(f"  Overall Pass:      {overall}/{total}")
    avg_conf = sum(r["confidence"] for r in results) / total if total else 0
    avg_time = sum(r["elapsed"] for r in results) / total if total else 0
    print(f"  Avg Confidence:    {avg_conf:.2f}")
    print(f"  Avg Response Time: {avg_time:.2f}s")
    print(f"{'=' * 80}")

    # Quick table
    print("\n  #  | Svc | Ans | Conf  | Time  | Status")
    print("  ---+-----+-----+-------+-------+-------")
    for r in results:
        s = "✓" if r["service_ok"] else "✗"
        a = "✓" if r["answer_ok"] else "✗"
        st = "PASS" if r["status"] else "FAIL"
        print(
            f"  {r['id']:2d} |  {s}  |  {a}  | "
            f"{r['confidence']:.2f}  | {r['elapsed']:4.1f}s | {st}"
        )
    print()


if __name__ == "__main__":
    run_tests()
