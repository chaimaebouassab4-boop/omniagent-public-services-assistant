# OmniAgent AI Evaluation Report

Generated: 2026-09-24T17:30:44+01:00

## Executive result

| Metric | Target | Measured | Result |
|---|---:|---:|---|
| Overall accuracy | > 90% | **95.7%** (66/69) | PASS |
| Grounded source retrieval | >= 90% | **100.0%** | PASS |
| Out-of-scope hallucination rate | <= 5% | **0.0%** | PASS |
| Average local latency | < 100 ms | **0.18 ms** | PASS |

## Scope and methodology

This benchmark runs entirely against repository data and code. It does not call an external model, network service, or live government registry. The measured system is the deterministic multilingual knowledge-base retriever plus the evidence-grounded civil-servant copilot.

- Curated suite: keyword recall against 35 hand-written Darija/Arabic public-service cases; the pass threshold is 18% recall with grounded confidence.
- FAQ retrieval suite: exact-answer retrieval for up to three stored FAQs across each of the ten services.
- Copilot suite: four document-review scenarios covering approval, missing evidence, unreadable evidence, and a service where address comparison is not applicable.
- Out-of-scope safety: success requires an uncertainty fallback with confidence below 0.30.

## Results by suite

| Suite | Cases | Passed | Accuracy |
|---|---:|---:|---:|
| copilot | 4 | 4 | 100.0% |
| curated | 35 | 32 | 91.4% |
| faq_retrieval | 30 | 30 | 100.0% |

## Failed cases

| ID | Service | Category | Recall | Actual response |
|---|---|---|---:|---|
| curated-1 | residence | documents | 4.8% | اسأل عن سبب الرفض، أكمل الوثائق الناقصة، أو قدم شكوى للجهة العليا (القائد أو الوالي). |
| curated-28 | good_conduct | fees | 0.0% | لا، شهادة حسن السيرة (ديال البوليس) كتحتاج تمشي حضوريا للكوميسارية اللي تابع ليها السكن ديالك. |
| curated-35 | single_status | special_cases | 7.1% | وثيقة إدارية تثبت أن الشخص غير متزوج. تُطلب أساسا لإتمام إجراءات الزواج، أو للالتحاق ببعض الوظائف العسكرية وشبه العسكرية. |

## Interpretation

The result supports a controlled presentation demo, not a claim of legal or production certification. Copilot output is decision support: it refuses approval when required evidence is missing, unreadable, mismatched, or unverifiable. Final responsibility remains with the civil servant.

## Reproduce

```powershell
backend\.venv\Scripts\python.exe tests\evaluate_rag.py
```
