from pathlib import Path
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

ROOT_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = ROOT_DIR / "chroma_db"

Settings.llm = Ollama(model="llama3.1:8b", base_url="http://localhost:11434", request_timeout=180.0)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="intfloat/multilingual-e5-large-instruct",
    query_instruction="query: ",
    text_instruction="passage: ",
)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))
col = client.get_or_create_collection("public_services_kb")

vector_store = ChromaVectorStore(chroma_collection=col)
index = VectorStoreIndex.from_vector_store(vector_store)

qe = index.as_query_engine(similarity_top_k=5)
print(qe.query("شنو الوثائق المطلوبة لشهادة السكنى فالمغرب؟"))