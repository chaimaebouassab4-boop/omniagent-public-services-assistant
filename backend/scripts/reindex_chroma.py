"""Safely rebuild the public-services ChromaDB index from the local KB.

Run from the repository root after adding or changing KB JSON/Markdown files:
    backend/.venv/Scripts/python.exe backend/scripts/reindex_chroma.py

Stop the backend first so Chroma does not hold open files on Windows.
"""
from __future__ import annotations

import gc
import os
import shutil
import sys
import uuid
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
CHROMA_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "public_services_kb"
EXCLUDED_NAMES = {"test_cases.json", "all_test_cases.json"}

sys.path.insert(0, str(BACKEND_DIR))
os.environ["ANONYMIZED_TELEMETRY"] = "False"


def load_documents():
    from llama_index.core import Document

    documents = []
    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
            continue
        if path.name in EXCLUDED_NAMES or "test_cases.json" in path.parts:
            continue
        relative = path.relative_to(KNOWLEDGE_DIR)
        service_type = relative.parts[0] if len(relative.parts) > 1 else "common"
        documents.append(
            Document(
                text=path.read_text(encoding="utf-8"),
                metadata={"file_path": str(path), "service_type": service_type},
            )
        )
    if not documents:
        raise RuntimeError(f"No knowledge documents found in {KNOWLEDGE_DIR}")
    return documents


def build_index(target_dir: Path) -> int:
    import chromadb
    from llama_index.core import Settings, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    # multilingual-e5-small: 117 MB, supports Arabic/French/Darija, fits Railway RAM
    Settings.embed_model = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small")
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)

    documents = load_documents()
    client = chromadb.PersistentClient(path=str(target_dir))
    collection = client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(documents, storage_context=storage, show_progress=True)
    count = collection.count()
    del collection, client
    gc.collect()
    print(f"[OK] Prepared {count} vectors from {len(documents)} knowledge files")
    return count


def replace_index(staged_dir: Path) -> None:
    backup_dir = ROOT_DIR / f".chroma_backup_{uuid.uuid4().hex}"
    had_existing = CHROMA_DIR.exists()
    try:
        if had_existing:
            CHROMA_DIR.rename(backup_dir)
        staged_dir.rename(CHROMA_DIR)
    except Exception:
        if had_existing and backup_dir.exists() and not CHROMA_DIR.exists():
            backup_dir.rename(CHROMA_DIR)
        raise
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def main() -> int:
    if not KNOWLEDGE_DIR.exists():
        print(f"[ERROR] Knowledge base not found: {KNOWLEDGE_DIR}")
        return 1
    staged_dir = ROOT_DIR / f".chroma_build_{uuid.uuid4().hex}"
    try:
        build_index(staged_dir)
        replace_index(staged_dir)
        print(f"[OK] ChromaDB refreshed at {CHROMA_DIR}")
        return 0
    except Exception as error:
        print(f"[ERROR] Re-indexing failed; existing ChromaDB was preserved: {error}")
        return 1
    finally:
        if staged_dir.exists():
            shutil.rmtree(staged_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
