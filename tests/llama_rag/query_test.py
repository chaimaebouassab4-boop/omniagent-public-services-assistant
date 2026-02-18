from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings

Settings.llm = Ollama(model="llama3.1:8b")

# تحميل الـ index الموجود
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_collection("public_admin_kb")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store)

# Query Engine بسيط
query_engine = index.as_query_engine()

# اختبار
response = query_engine.query("شنو الوثائق المطلوبة لشهادة السكنى إلا كنت مستأجر؟")
print(response)