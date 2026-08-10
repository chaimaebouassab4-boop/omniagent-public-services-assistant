"""Unit test for RAG service module (backend/app/rag_service.py)"""
import sys
from pathlib import Path

# Add project root and backend to python path
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

from app.rag_service import query_rag, OmniAgentRAG

def main():
    print("[TEST] Testing RAG Service Module...")
    
    test_queries = [
        ("شنو الوثائق المطلوبة لشهادة السكنى؟", "residence"),
        ("كيفاش نخرج عقد الازدياد أونلاين؟", "birth"),
        ("شنو الفرق بين حسن السيرة والسجل العدلي؟", None),
    ]

    for query, service in test_queries:
        print("\n" + "=" * 60)
        print(f"Query: {query} (Service filter: {service})")
        res = query_rag(user_query=query, service_type=service)
        print(f"Answer: {res.get('answer')}")
        print(f"Confidence: {res.get('confidence')}")
        print(f"Sources: {res.get('sources')}")
        print(f"Language: {res.get('language')}")
        if res.get('fallback_reason'):
            print(f"Fallback reason: {res.get('fallback_reason')}")

    print("\n[OK] RAG Service Module Test Complete!")

if __name__ == "__main__":
    main()
