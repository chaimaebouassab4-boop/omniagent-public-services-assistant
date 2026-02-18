# build_index.py
from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# 1. إعدادات عامة
Settings.llm = Ollama(model="llama3.1:8b", request_timeout=180.0, base_url="http://localhost:11434")

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1"
)

# 2. المسار ديال knowledge_base (عدل إلا المسار مختلف)
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge_base"   # يرجع خطوتين للـ root ثم knowledge_base

# 3. قراءة كل الملفات داخل knowledge_base
documents = SimpleDirectoryReader(
    input_dir=KNOWLEDGE_DIR,
    required_exts=[".json", ".md"],   # نقرا JSON و Markdown فقط
    recursive=True
).load_data()

print(f"تم تحميل {len(documents)} وثيقة")

# 4. إعداد Chroma (vector database محلية)
chroma_path = Path(__file__).parent / "chroma_db"
chroma_client = chromadb.PersistentClient(path=str(chroma_path))
chroma_collection = chroma_client.get_or_create_collection("public_services_kb")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 5. بناء الـ index
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    show_progress=True
)

print("تم بناء الـ index وحفظه في مجلد chroma_db !")