"""Optional interactive LlamaIndex/Ollama smoke test.

The optional model and network setup intentionally lives inside ``main`` so
pytest can collect the repository without downloading BGE-M3 or requiring a
running Ollama server.
"""
from __future__ import annotations

import sys
from pathlib import Path


QUESTIONS = [
    "شنو الوثائق المطلوبة لشهادة السكنى فالمغرب؟",
    "كيفاش نخرج عقد الازدياد أونلاين؟",
    "من يقدر يصرح بالوفاة وكم الأجل القانوني؟",
    "شنو الوثائق المطلوبة لعقد الزواج؟",
    "واش ضروري نحضر شخصيا باش ناخد شهادة الحياة؟",
    "شنو هما الوثائق المطلوبة لشهادة العزوبة؟",
    "واش ضروري نمشي لدار الضريبة باش ناخد شهادة عدم الملكية؟",
    "واش ضروري المقدم يدير بحث باش يعطيوها ليا؟",
    "واش نقدر ناخد شهادة حسن السيرة أونلاين؟",
    "شنو الفرق بين حسن السيرة والسجل العدلي؟",
]


def print_arabic(text: str) -> None:
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        print(text)
        return
    print(get_display(arabic_reshaper.reshape(text)))


def main() -> None:
    import chromadb
    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.ollama import Ollama
    from llama_index.vector_stores.chroma import ChromaVectorStore

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root_dir = Path(__file__).resolve().parents[2]
    chroma_dir = root_dir / "chroma_db"

    Settings.llm = Ollama(
        model="llama3.2:3b",
        request_timeout=360.0,
        base_url="http://localhost:11434",
        context_window=8192,
        temperature=0.1,
    )
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection("public_services_kb")
    print("CHROMA_DIR:", chroma_dir)
    print("COLLECTION:", collection.name)
    print("COUNT:", collection.count())

    index = VectorStoreIndex.from_vector_store(
        ChromaVectorStore(chroma_collection=collection)
    )
    query_engine = index.as_query_engine(similarity_top_k=3)

    for question in QUESTIONS:
        print("\n" + "=" * 80)
        print_arabic("Q: " + question)
        try:
            print_arabic("A: " + str(query_engine.query(question)))
        except Exception as exc:  # interactive diagnostic only
            print("ERROR:", exc)


if __name__ == "__main__":
    main()
