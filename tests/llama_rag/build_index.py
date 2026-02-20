# build_index.py
from pathlib import Path
import os
import shutil

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter

# 0) Stop Chroma telemetry warning
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 1) Resolve ROOT directory (خدام حتى إلا كنتي ف tests/llama_rag/)
THIS_FILE = Path(__file__).resolve()
ROOT_DIR = THIS_FILE.parents[2]  # adjust if your structure differs

# 2) Knowledge base folder (root/knowledge_base)
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
if not KNOWLEDGE_DIR.exists():
    raise FileNotFoundError(f"knowledge_base not found at: {KNOWLEDGE_DIR}")

# 3) Stable Chroma path (IMPORTANT)
CHROMA_DIR = ROOT_DIR / "chroma_db"

# ⚠️ مهم: إلا كنتي غادي تبدلي embedding model، مسحي DB القديمة
# (ديريها غير مرة وحدة ملي تبدلي الموديل)
RESET_DB = False  # خليها True غير فاش تبدلي embedding
if RESET_DB and CHROMA_DIR.exists():
    shutil.rmtree(CHROMA_DIR)

# 4) LLM (Ollama)
Settings.llm = Ollama(
    model="llama3.1:8b",
    request_timeout=180.0,
    base_url="http://localhost:11434",
)

# 5) Embeddings (Local + Arabic/Darija friendly)
# e5 instruct models work better with query/passage instructions
Settings.embed_model = HuggingFaceEmbedding(
    model_name="intfloat/multilingual-e5-large-instruct",
    query_instruction="query: ",
    text_instruction="passage: ",
)

# 6) Chunking (important for Arabic retrieval)
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

# 7) Load documents
documents = SimpleDirectoryReader(
    input_dir=str(KNOWLEDGE_DIR),
    recursive=True,
    required_exts=[".json", ".md"],
).load_data()

print(f"Loaded {len(documents)} documents from: {KNOWLEDGE_DIR}")

# 8) Chroma persistent store (one single client, one single path)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection("public_services_kb")

vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 9) Build index (writes to Chroma)
index = VectorStoreIndex.from_documents(
    documents=documents,
    storage_context=storage_context,
    show_progress=True,
)

print(f"✅ Index built. Chroma path: {CHROMA_DIR}")
print(f"✅ Collection: public_services_kb | COUNT: {collection.count()}")