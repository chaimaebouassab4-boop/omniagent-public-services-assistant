"""Test the exact 4 queries from the UI."""
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding='utf-8')

from app.rag_service import query_rag

def main():
    queries = [
        "واش الشهادة الإدارية ضرورية للزواج؟",
        "شنو هي الوثائق اللي خصني نجيب لشهادة السكنى؟",
        "بغيت نسول على رخصة تجارية",
        "كيفاش نجدد بطاقة التعريف؟"
    ]

    for q in queries:
        print("\n" + "=" * 60)
        print(f"Q: {q}")
        res = query_rag(q)
        print(f"A: {res.get('answer')}")
        print(f"Confidence: {res.get('confidence')}")
        print(f"Sources: {res.get('sources')}")

if __name__ == "__main__":
    main()
