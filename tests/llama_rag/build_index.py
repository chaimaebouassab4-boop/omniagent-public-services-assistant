# build_index.py
import sys
import os
import json
import shutil
from pathlib import Path

# Force UTF-8 for Windows Terminal
sys.stdout.reconfigure(encoding='utf-8')

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    PromptTemplate,
    Document
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter

# 0) Disable Chroma telemetry warning
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# 1) Resolve paths
THIS_FILE = Path(__file__).resolve()
ROOT_DIR = THIS_FILE.parents[2]  # omniagent-public-services-assistant/
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
CHROMA_DIR = ROOT_DIR / "chroma_db"

if not KNOWLEDGE_DIR.exists():
    raise FileNotFoundError(f"Knowledge base not found at: {KNOWLEDGE_DIR}")

# Optional: Reset DB if needed
RESET_DB = True
if RESET_DB and CHROMA_DIR.exists():
    print(f"🗑️ Deleting existing Chroma database at {CHROMA_DIR}...")
    shutil.rmtree(CHROMA_DIR)

# 2) Setup models (LLM and Embeddings)
print("⚙️ Configuring models...")
Settings.llm = Ollama(
    model="llama3.1:8b", # Assuming llama3.1:8b as default for RAG pipeline
    request_timeout=180.0,
    base_url="http://localhost:11434",
    temperature=0.1
)

# HuggingFace embeddings - Using BGE-M3 which is state-of-the-art for Arabic/Multilingual (including Darija)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-m3"
)

# 3) Setup chunking
print("✂️ Configuring sentence splitter...")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

# 4) Load documents using Python's open to GUARANTEE utf-8 encoding on Windows
print(f"📂 Loading documents from {KNOWLEDGE_DIR}...")
documents = []
for file_path in KNOWLEDGE_DIR.rglob("*"):
    # Exclude test case files from knowledge indexing
    if file_path.name == "test_cases.json" or file_path.name == "all_test_cases.json":
        continue
        
    if file_path.suffix in [".json", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Create LlamaIndex Document directly
            documents.append(Document(text=content, metadata={"file_path": str(file_path)}))
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

print(f"✅ Loaded {len(documents)} document chunks from knowledge base.")

# 4.5) إضافة metadata لكل document (مهم جدا للـ Filtering!)
print("🏷️ Injecting metadata into documents...")
for doc in documents:
    file_path = Path(doc.metadata.get("file_path", ""))
    
    # هنا غادي نردو الكود ديناميكي: أي دوسي حطيتي فيه الـ JSON غيتعتابر Service Type!
    if KNOWLEDGE_DIR in file_path.parents:
        # كيجيب السمية ديال الدوسي اللي تحت knowledge_base مباشرة (مثال: residence, birth, marriage, ramid...)
        relative_path = file_path.relative_to(KNOWLEDGE_DIR)
        category = relative_path.parts[0] if len(relative_path.parts) > 0 else "common"
        doc.metadata["service_type"] = category
    else:
        doc.metadata["service_type"] = "common"

# 5) Setup vector store and index
print("🗄️ Initializing ChromaDB vector store...")
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection("public_services_kb")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("🏗️ Building vector index...")
index = VectorStoreIndex.from_documents(
    documents=documents,
    storage_context=storage_context,
    show_progress=True,
)
print(f"✅ Index built. Collection 'public_services_kb' contains {collection.count()} elements.")

# 6) Custom Prompt for Retrieval
QA_PROMPT_TMPL = (
    "المعلومات المتوفرة (sources):\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "أنت مساعد افتراضي مغربي. بناءً على المعلومات الفوق فقط، جاوب بالدارجة المغربية على السؤال التالي.\n"
    "مهم جداً: إذا كانت المعلومات لا تحتوي على الجواب أو كنت غير متأكد، قل حرفياً وبدون أي زيادة: \"ما متأكدش\" واطلب توضيح.\n"
    "لا تستخدم معلومات من خارج النص المتوفر.\n"
    "السؤال: {query_str}\n"
    "الجواب: "
)
qa_prompt = PromptTemplate(QA_PROMPT_TMPL)

# 7) Query Engine
print("\n🔍 Setting up the custom Query Engine...")
query_engine = index.as_query_engine(
    similarity_top_k=3,
    text_qa_template=qa_prompt
)

# 8) Test with test_cases.json if available
print("\n🧪 Running Tests...")
test_files = list(Path(KNOWLEDGE_DIR).rglob("test_cases.json"))

if not test_files:
    print("⚠️ No test_cases.json found. Running default demo queries.")
    default_queries = [
        "شنو هما الوثائق المطلوبة لشهادة السكنى؟",
        "كم رسوم عقد الازدياد؟",
        "شنو هي شروط السفر للقمر؟" # Testing the 'not sure' logic
    ]
    for q in default_queries:
        print(f"\nسؤال: {q}")
        response = query_engine.query(q)
        print(f"جواب RAG: {response}")
        print("-" * 50)
else:
    for tf in test_files:
        if not tf.is_file():
            continue
        print(f"➡️ Testing file: {tf.name} in {tf.parent.name}")
        try:
            with open(tf, "r", encoding="utf-8") as f:
                cases = json.load(f)
                
            # Allow structured test cases (dict or list)
            if isinstance(cases, dict) and "test_cases" in cases:
                cases = cases["test_cases"]
                
            for case in cases:
                if isinstance(case, dict) and "query" in case:
                    q = case["query"]
                    exp = case.get("expected", "N/A")
                    print(f"\nسؤال: {q}")
                    print(f"المتوقع: {exp}")
                    response = query_engine.query(q)
                    print(f"جواب RAG: {response}")
                    print("-" * 50)
        except Exception as e:
            print(f"❌ Error reading {tf}: {e}")

print("\n🎉 Pipeline complete!")