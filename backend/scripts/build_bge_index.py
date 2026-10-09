"""Safely rebuild the section-level BGE-M3 Chroma index.

Run from the repository root:
    python backend/scripts/build_bge_index.py
"""
from __future__ import annotations

import argparse
import gc
import os
import shutil
import sys
import uuid
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
CHROMA_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "public_services_kb"
DEFAULT_MODEL = "BAAI/bge-m3"
REQUIRED_CHUNK_METADATA = {
    "procedure_id", "section", "language", "source_type",
    "file_path", "service_type", "node_type",
}

sys.path.insert(0, str(BACKEND_DIR))
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from app.services.procedure_schema import (  # noqa: E402
    generate_procedure_chunks,
    iter_normalized_procedures,
)


def load_chunks(procedure_ids: set[str] | None = None):
    chunks = []
    for procedure, path in iter_normalized_procedures():
        if procedure_ids and procedure["procedure_id"] not in procedure_ids:
            continue
        chunks.extend(generate_procedure_chunks(procedure, path))
    if not chunks:
        raise RuntimeError("No procedure chunks were generated")
    return chunks


def audit_chunks(chunks) -> tuple[int, int]:
    """Return counts of chunks with missing metadata and invalid payloads."""
    missing_metadata = 0
    invalid_chunks = 0
    seen_ids: set[str] = set()
    for chunk in chunks:
        if REQUIRED_CHUNK_METADATA - set(chunk.metadata):
            missing_metadata += 1
        if (
            not chunk.chunk_id
            or chunk.chunk_id in seen_ids
            or not chunk.text.strip()
            or not chunk.metadata.get("procedure_id")
            or not chunk.metadata.get("section")
        ):
            invalid_chunks += 1
        seen_ids.add(chunk.chunk_id)
    return missing_metadata, invalid_chunks


def build_index(target_dir: Path, model_name: str, procedure_ids: set[str] | None = None) -> tuple[int, Counter]:
    import chromadb
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer

    chunks = load_chunks(procedure_ids)
    missing_metadata, invalid_chunks = audit_chunks(chunks)
    print(f"[AUDIT] Missing required metadata: {missing_metadata}")
    print(f"[AUDIT] Invalid chunks: {invalid_chunks}")
    if missing_metadata or invalid_chunks:
        raise RuntimeError("Chunk audit failed; existing ChromaDB was preserved")
    print(f"[INDEX] Loading embedding model: {model_name}")
    try:
        model_source = snapshot_download(
            repo_id=model_name,
            local_files_only=True,
        )
        model = SentenceTransformer(model_source, local_files_only=True)
    except Exception:
        # Preserve first-time setup behavior when the model is not cached.
        model = SentenceTransformer(model_name)
    client = chromadb.PersistentClient(path=str(target_dir))
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": model_name,
            "schema_version": "2",
        },
    )

    batch_size = 24
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        texts = [chunk.text for chunk in batch]
        embeddings = model.encode(
            texts,
            batch_size=8,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        collection.add(
            ids=[chunk.chunk_id for chunk in batch],
            documents=texts,
            metadatas=[chunk.metadata for chunk in batch],
            embeddings=embeddings,
        )
        print(f"[INDEX] Embedded {min(start + len(batch), len(chunks))}/{len(chunks)} chunks")

    count = collection.count()
    by_procedure = Counter(chunk.metadata["procedure_id"] for chunk in chunks)
    del collection, client, model
    gc.collect()
    return count, by_procedure


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


def replace_collection_in_place(staged_dir: Path) -> None:
    """Install a staged collection when OneDrive blocks directory renames."""
    import chromadb

    staged_client = chromadb.PersistentClient(path=str(staged_dir))
    staged_collection = staged_client.get_collection(COLLECTION_NAME)
    payload = staged_collection.get(include=["documents", "metadatas", "embeddings"])

    target_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if COLLECTION_NAME in {item.name for item in target_client.list_collections()}:
        target_client.delete_collection(COLLECTION_NAME)
    target_collection = target_client.create_collection(
        COLLECTION_NAME,
        metadata=dict(staged_collection.metadata or {"hnsw:space": "cosine"}),
    )
    embeddings = payload.get("embeddings")
    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()
    ids = payload.get("ids") or []
    for start in range(0, len(ids), 50):
        stop = start + 50
        target_collection.add(
            ids=ids[start:stop],
            documents=(payload.get("documents") or [])[start:stop],
            metadatas=(payload.get("metadatas") or [])[start:stop],
            embeddings=(embeddings or [])[start:stop],
        )
    if target_collection.count() != staged_collection.count():
        raise RuntimeError("In-place Chroma replacement count mismatch")
    del target_collection, target_client, staged_collection, staged_client
    gc.collect()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--procedures", nargs="*", help="Optional canonical procedure ids")
    args = parser.parse_args(argv)
    staged_dir = ROOT_DIR / f".chroma_build_{uuid.uuid4().hex}"
    try:
        count, by_procedure = build_index(
            staged_dir,
            args.model,
            set(args.procedures) if args.procedures else None,
        )
        try:
            replace_index(staged_dir)
        except PermissionError as error:
            print(f"[WARN] Directory swap blocked ({error}); replacing collection in place.")
            replace_collection_in_place(staged_dir)
        print(f"[OK] Collection: {COLLECTION_NAME}")
        print("[OK] Distance: cosine")
        print(f"[OK] Total chunks: {count}")
        for procedure_id, procedure_count in sorted(by_procedure.items()):
            print(f"[OK] {procedure_id}: {procedure_count}")
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
