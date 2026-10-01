"""Build a NEW cosine/BGE collection; never overwrite an existing index."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import chromadb
    from sentence_transformers import SentenceTransformer
    from app.rag_service import _load_kb_nodes, ROOT_DIR
    from app.services.vector_retrieval import MODEL, COLLECTION

    client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", str(ROOT_DIR / "chroma_db")))
    name = os.getenv("CHROMA_COLLECTION", COLLECTION)
    if name in [c.name for c in client.list_collections()]:
        raise RuntimeError("Collection already exists. Set CHROMA_COLLECTION to a new version name.")
    nodes = _load_kb_nodes()
    if not nodes:
        raise RuntimeError("No knowledge loaded")
    encoder = SentenceTransformer(MODEL)
    collection = client.create_collection(name, embedding_function=None,
        metadata={"hnsw:space": "cosine", "embedding_model": MODEL, "build_complete": False})
    # Bound long Markdown nodes; include every source and preserve overlap.
    chunks = [(node.text[start:start + 2400], node.metadata)
              for node in nodes for start in range(0, len(node.text), 2100)]
    for offset in range(0, len(chunks), 16):
        batch = chunks[offset:offset + 16]
        texts = [text for text, _ in batch]
        vectors = encoder.encode(texts, normalize_embeddings=True).tolist()
        collection.add(ids=[str(offset + i) for i in range(len(batch))],
                       documents=texts, metadatas=[meta for _, meta in batch], embeddings=vectors)
    # Mark build complete while preserving hnsw:space: cosine.
    # Note: Chroma rejects 'hnsw:space' in collection.modify() and strips it if omitted.
    try:
        import sqlite3
        db_path = Path(os.getenv("CHROMA_PATH", str(ROOT_DIR / "chroma_db"))) / "chroma.sqlite3"
        if db_path.exists():
            with sqlite3.connect(db_path) as con:
                col_id = str(collection.id)
                con.execute(
                    "INSERT OR REPLACE INTO collection_metadata (collection_id, key, int_value, bool_value) VALUES (?, 'build_complete', NULL, 1)",
                    (col_id,)
                )
                con.execute(
                    "INSERT OR REPLACE INTO collection_metadata (collection_id, key, str_value) VALUES (?, 'hnsw:space', 'cosine')",
                    (col_id,)
                )
                con.commit()
    except Exception as err:
        print(f"[WARN] SQLite metadata update: {err}")
    print(f"Built {collection.count()} chunks in {name}. Set RAG_BACKEND=chroma and restart backend.")


if __name__ == "__main__":
    main()
