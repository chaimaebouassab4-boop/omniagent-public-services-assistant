import sys
from pathlib import Path
import chromadb

# Force UTF-8 for Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------------------------------------------
# Arabic Terminal Fix (Reshaping + BiDi)
# ---------------------------------------------------------
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    CAN_RESHAPE = True
except ImportError:
    CAN_RESHAPE = False
    print("⚠️  لتصحيح الحروف العربية في الـ Terminal، قم بتشغيل:")
    print("pip install arabic-reshaper python-bidi\n")

def print_arabic(text):
    if CAN_RESHAPE and isinstance(text, str):
        # Reshape the text to join Arabic letters
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply BiDi algorithm for correct Right-To-Left display
        bidi_text = get_display(reshaped_text)
        print(bidi_text)
    else:
        print(text)
# ---------------------------------------------------------

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

# 6) Tests (اختبارات تشمل 10 خدمات)
questions = [
    # 1. شهادة السكنى (Residence)
    "شنو الوثائق المطلوبة لشهادة السكنى فالمغرب؟",
    
    # 2. عقد الازدياد (Birth)
    "كيفاش نخرج عقد الازدياد أونلاين؟",
    
    # 3. مستخرج شهادة الوفاة (Death)
    "من يقدر يصرح بالوفاة وكم الأجل القانوني؟",

    # 4. عقد الزواج (Marriage)
    "شنو الوثائق المطلوبة لعقد الزواج؟",
    
    # 5. شهادة الحياة (Life)
    "واش ضروري نحضر شخصيا باش ناخد شهادة الحياة؟",

    # 6. شهادة العزوبة (Single Status)
    "شنو هما الوثائق المطلوبة لشهادة العزوبة؟",

    # 7. شهادة عدم الملكية (Non-Property)
    "واش ضروري نمشي لدار الضريبة باش ناخد شهادة عدم الملكية؟",

    # 8. الشهادة الإدارية (Administrative)
    "واش ضروري المقدم يدير بحث باش يعطيوها ليا؟",

    # 9. شهادة حسن السيرة (Good Conduct)
    "واش نقدر ناخد شهادة حسن السيرة أونلاين؟",

    # 10. السجل العدلي (Criminal Record)
    "شنو الفرق بين حسن السيرة والسجل العدلي؟"
]

for q in questions:
    print("\n" + "=" * 80)
    print_arabic("Q: " + q)
    try:
        ans = qe.query(q)
        print_arabic("A: " + str(ans))
    except Exception as e:
        print("❌ ERROR:", e)