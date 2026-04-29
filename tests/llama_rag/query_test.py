import sys
from pathlib import Path
import chromadb

# Force UTF-8 for Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1) Root dir (باش نخدمو بنفس chroma_db ديال build_index.py)
THIS_FILE = Path(__file__).resolve()
ROOT_DIR = THIS_FILE.parents[2]  # omniagent-public-services-assistant/
CHROMA_DIR = ROOT_DIR / "chroma_db"

# 2) LLM (خفيف باش ما يطيحش RAM، مع context window hardcoded باش نتجنبو errors ديال metadata)
Settings.llm = Ollama(
    model="llama3.2:3b",          # بدليه إذا بغيتي: "phi3:mini" أو "qwen2:0.5b" إلا RAM ضعيف جدا
    request_timeout=360.0,        # زدنا timeout إلا كان Ollama بطيء
    base_url="http://localhost:11434",
    context_window=8192,          # Hardcode باش نتجنبو detection errors
    temperature=0.1               # Low باش الإجابات تكون دقيقة ف RAG
)

# 3) Embeddings (لازم EXACT نفس اللي بنيتي به index: BAAI/bge-m3)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-m3",
)

# 4) Load Chroma collection
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection("public_services_kb")

print("✅ CHROMA_DIR:", CHROMA_DIR)
print("✅ COLLECTION:", collection.name)
print("✅ COUNT:", collection.count())

vector_store = ChromaVectorStore(chroma_collection=collection)
index = VectorStoreIndex.from_vector_store(vector_store)

# 5) Query engine (حددنا top_k صغير باش نتجنبو context overflow + RAM issues)
qe = index.as_query_engine(
    similarity_top_k=3,  # 3 غير كافي مع 10 docs total، يقلل context size
)

# 6) Tests (بدلي الأسئلة اللي بغيتي)
questions = [
    # أسئلة شهادة السكنى
    "شنو الوثائق المطلوبة لشهادة السكنى فالمغرب؟",
    "فين كنقدم طلب شهادة السكنى؟",
    "شحال كتاخذ من الوقت شهادة السكنى؟",
    "واش كاين شي رسوم ولا لا؟",
    
    # أسئلة عقد الازدياد (جديد)
    "شنو هما الوثائق المطلوبة باش نطلب عقد الازدياد؟",
    "كيفاش نخرج عقد الازدياد أونلاين؟",
    "شحال الثمن ديال عقد الازدياد؟",
    "واش ممكن نطلب عقد الازدياد فالمقاطعة؟",
    
    # أسئلة عقد الزواج (جديد)
    "شنو الوثائق المطلوبة لعقد الزواج؟",
    "فين كنصايبو عقد الزواج؟",
    "شحال كيكلف عقد الزواج فالمغرب؟",
]

for q in questions:
    print("\n" + "=" * 80)
    print("Q:", q)
    try:
        ans = qe.query(q)
        print("A:", ans)
    except Exception as e:
        print("❌ ERROR:", e)