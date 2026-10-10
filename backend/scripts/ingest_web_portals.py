#!/usr/bin/env python3
"""Web Ingestion & Knowledge Base Pipeline
==========================================

Scrapes official Moroccan public-service portals, chunks the content
semantically, and upserts it into the shared ChromaDB collection
``public_services_kb`` using the same BAAI/bge-m3 embedding model
that the RAG engine uses at query time — so no index rebuild is needed.

Usage
-----
    # Ingest all configured portal URLs
    python backend/scripts/ingest_web_portals.py

    # Ingest only specific target keys
    python backend/scripts/ingest_web_portals.py --targets residence birth

    # Dry-run: scrape + chunk but do NOT write to ChromaDB
    python backend/scripts/ingest_web_portals.py --dry-run

    # Show what is already in the collection
    python backend/scripts/ingest_web_portals.py --stats

    # Force re-ingest even if URLs are already indexed
    python backend/scripts/ingest_web_portals.py --force

Architecture
------------
    Portal URL(s)
        │
        ▼
    HTTP fetch (requests + User-Agent rotation)
        │
        ▼
    HTML → clean text  (BeautifulSoup — main article body only)
        │
        ▼
    Sentence-aware chunking  (chunk_size=1000, chunk_overlap=200)
        │
        ▼
    BAAI/bge-m3 embeddings  (same model as RAG engine)
        │
        ▼
    ChromaDB upsert  (collection: public_services_kb)
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys
import time
import uuid
from dataclasses import dataclass, field

# ─── Windows console UTF-8 fix ───────────────────────────────────────────────
# PowerShell uses cp1252 by default; force UTF-8 so Arabic chars print cleanly.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from typing import Optional

# ─── Path setup — allows `from app.*` imports ────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent          # backend/scripts/
_BACKEND_DIR = _SCRIPT_DIR.parent                      # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                    # omniagent-public-services-assistant/

sys.path.insert(0, str(_BACKEND_DIR))                  # exposes `app` package

from app.services.procedure_schema import PROCEDURE_IDS_BY_DIR  # noqa: E402

CHROMA_DIR  = _PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "public_services_kb"

# ─── Target Portal Configurations ────────────────────────────────────────────
#
# Each entry describes ONE logical topic to scrape.
# 'urls'         → list of pages to fetch (each page = one document)
# 'service_type' → folder-name metadata key  (matches rag_service.py convention)
# 'label_ar'     → human-readable Arabic label (stored in metadata)
#
PORTAL_TARGETS: list[dict] = [
    # ── Residence Certificate ─────────────────────────────────────────────────
    # service-public.ma returns 403, use cached/open alternatives
    {
        "key": "residence",
        "service_type": "residence",
        "label_ar": "شهادة السكنى",
        "urls": [
            # Wikipedia Morocco articles (open, no bot-blocking)
            "https://fr.wikipedia.org/wiki/Administration_publique_marocaine",
            "https://ar.wikipedia.org/wiki/%D8%A7%D9%84%D8%AA%D8%B4%D9%87%D9%8A%D8%AF%D8%A7%D8%AA_%D8%A7%D9%84%D8%A5%D8%AF%D8%A7%D8%B1%D9%8A%D8%A9_%D9%81%D9%8A_%D8%A7%D9%84%D9%85%D8%BA%D8%B1%D8%A8",
        ],
    },
    # ── Birth Certificate ─────────────────────────────────────────────────────
    {
        "key": "birth",
        "service_type": "birth",
        "label_ar": "عقد الازدياد",
        "urls": [
            "https://fr.wikipedia.org/wiki/Registre_d%27%C3%A9tat_civil",
            "https://ar.wikipedia.org/wiki/%D8%B3%D8%AC%D9%84_%D8%A7%D9%84%D8%AD%D8%A7%D9%84%D8%A9_%D8%A7%D9%84%D9%85%D8%AF%D9%86%D9%8A%D8%A9",
        ],
    },
    # ── Death Certificate ─────────────────────────────────────────────────────
    {
        "key": "death",
        "service_type": "death",
        "label_ar": "شهادة الوفاة",
        "urls": [
            "https://fr.wikipedia.org/wiki/Acte_de_d%C3%A9c%C3%A8s",
        ],
    },
    # ── Criminal Record ───────────────────────────────────────────────────────
    {
        "key": "criminal_record",
        "service_type": "criminal_record",
        "label_ar": "السجل العدلي",
        "urls": [
            "https://fr.wikipedia.org/wiki/Casier_judiciaire",
        ],
    },
    # ── Marriage Certificate ──────────────────────────────────────────────────
    {
        "key": "marriage",
        "service_type": "marriage",
        "label_ar": "عقد الزواج",
        "urls": [
            "https://fr.wikipedia.org/wiki/Acte_de_mariage",
            "https://ar.wikipedia.org/wiki/%D8%B9%D9%82%D8%AF_%D8%A7%D9%84%D8%B2%D9%88%D8%A7%D8%AC",
        ],
    },
    # ── CIN / National Identity Card ─────────────────────────────────────────
    {
        "key": "cin",
        "service_type": "cin",
        "label_ar": "البطاقة الوطنية للتعريف",
        "urls": [
            "https://fr.wikipedia.org/wiki/Carte_nationale_d%27identit%C3%A9_(Maroc)",
            "https://ar.wikipedia.org/wiki/%D8%A8%D8%B7%D8%A7%D9%82%D8%A9_%D8%A7%D9%84%D8%AA%D8%B9%D8%B1%D9%8A%D9%81_%D8%A7%D9%84%D9%88%D8%B7%D9%86%D9%8A%D8%A9_%D8%A7%D9%84%D9%85%D8%BA%D8%B1%D8%A8%D9%8A%D8%A9",
        ],
    },
    # ── Passport ─────────────────────────────────────────────────────────────
    {
        "key": "passport",
        "service_type": "passport",
        "label_ar": "جواز السفر",
        "urls": [
            "https://fr.wikipedia.org/wiki/Passeport_marocain",
            "https://ar.wikipedia.org/wiki/%D8%AC%D9%88%D8%A7%D8%B2_%D8%A7%D9%84%D8%B3%D9%81%D8%B1_%D8%A7%D9%84%D9%85%D8%BA%D8%B1%D8%A8%D9%8A",
        ],
    },
]

# ─── NOTE: service-public.ma Portal Targets (403 blocked — requires a session)
# To ingest service-public.ma, either:
#   1. Open the page in a browser, save as HTML, then use --local-html flag (future feature).
#   2. Use the --seed-from-kb flag to convert existing JSON knowledge base files to vectors.
#   3. Use the --seed-from-kb flag (recommended — works offline with your existing data).
#
# The Wikipedia URLs above provide supplementary encyclopedic context.
# Your existing tests/knowledge_base/*.json files are the primary accurate source.


# ─── HTTP request headers (polite scraper) ────────────────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-MA,fr;q=0.9,ar;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_REQUEST_DELAY_SECS = 1.5   # polite crawl rate


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ScrapedPage:
    url: str
    title: str
    body_text: str
    service_type: str
    label_ar: str
    source_key: str


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    metadata: dict = field(default_factory=dict)


# ─── Step 1: HTTP Fetch + HTML Cleaning ──────────────────────────────────────

def fetch_page(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch a URL and return raw HTML, or None on failure."""
    try:
        import requests

        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception as exc:
        print(f"  [WARN] Could not fetch {url}: {exc}")
        return None


def html_to_text(html: str, url: str) -> tuple[str, str]:
    """Extract clean text and page title from raw HTML.

    Strategy:
    1. Try to find the main article / content div (service-public.ma layout).
    2. Fall back to <main>, then <body> if no article found.
    3. Strip nav, footer, script, style tags.

    Returns (title, body_text).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "BeautifulSoup4 is not installed. "
            "Run: pip install beautifulsoup4 lxml"
        )

    soup = BeautifulSoup(html, "lxml")

    # Remove boilerplate elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "button", "noscript", "iframe"]):
        tag.decompose()

    # Page title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    # Try common content containers used by service-public.ma
    content = None
    for selector in [
        "article",
        "div.field-body",
        "div.field--type-text-with-summary",
        "div.views-element-container",
        "div#content",
        "div.content",
        "main",
    ]:
        content = soup.select_one(selector)
        if content and len(content.get_text(strip=True)) > 200:
            break

    if not content:
        content = soup.body or soup

    # Get clean text — preserve line breaks between block elements
    lines = []
    for element in content.find_all(
        ["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "dt", "dd"]
    ):
        text = element.get_text(separator=" ", strip=True)
        if text and len(text) > 10:
            lines.append(text)

    # Fallback: get_text if no structured tags found
    if not lines:
        lines = [content.get_text(separator="\n", strip=True)]

    body = "\n".join(lines)
    # Collapse excessive whitespace
    import re
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return title, body


def scrape_target(target: dict) -> list[ScrapedPage]:
    """Fetch and clean all URLs for one service target. Returns list of ScrapedPage."""
    pages = []
    for url in target["urls"]:
        print(f"  Fetching: {url}")
        html = fetch_page(url)
        if not html:
            continue
        try:
            title, body = html_to_text(html, url)
        except Exception as exc:
            print(f"  [WARN] Parsing failed for {url}: {exc}")
            continue

        if len(body.strip()) < 100:
            print(f"  [SKIP] Too little content extracted from {url} ({len(body)} chars)")
            continue

        print(f"  [OK] '{title}' — {len(body)} chars extracted")
        pages.append(ScrapedPage(
            url=url,
            title=title,
            body_text=body,
            service_type=target["service_type"],
            label_ar=target["label_ar"],
            source_key=target["key"],
        ))
        time.sleep(_REQUEST_DELAY_SECS)
    return pages


# ─── Step 2: Semantic Chunking ────────────────────────────────────────────────

def chunk_page(page: ScrapedPage, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[TextChunk]:
    """Split a ScrapedPage body into overlapping text chunks.

    Uses a simple sentence-boundary splitter that:
    1. Splits on sentence-ending punctuation (. ! ? ، ؟).
    2. Accumulates sentences into chunks of ≤ chunk_size characters.
    3. Back-tracks chunk_overlap characters for context continuity.
    """
    import re

    text = page.body_text
    # Split into sentences on Arabic and Latin punctuation
    sentence_endings = re.compile(r"(?<=[.!?؟،\n])\s+")
    sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]

    chunks: list[TextChunk] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)

        # If a single sentence is longer than chunk_size, hard-split it
        if s_len > chunk_size:
            # Flush current buffer first
            if current:
                _flush_chunk(chunks, page, " ".join(current))
                current = []
                current_len = 0
            # Hard split the long sentence
            for i in range(0, s_len, chunk_size - chunk_overlap):
                sub = sentence[i:i + chunk_size]
                _flush_chunk(chunks, page, sub)
            continue

        if current_len + s_len + 1 > chunk_size:
            # Flush
            _flush_chunk(chunks, page, " ".join(current))
            # Carry over the overlap window
            overlap_text = " ".join(current)[-chunk_overlap:].strip()
            current = [overlap_text, sentence] if overlap_text else [sentence]
            current_len = len(overlap_text) + s_len + 1
        else:
            current.append(sentence)
            current_len += s_len + 1

    if current:
        _flush_chunk(chunks, page, " ".join(current))

    return chunks


def _flush_chunk(chunks: list[TextChunk], page: ScrapedPage, text: str) -> None:
    """Create a TextChunk with a stable content-hash ID and append to list."""
    text = text.strip()
    if len(text) < 40:          # ignore very short artefacts
        return
    chunk_id = "web_" + hashlib.md5(
        (page.url + text[:200]).encode("utf-8")
    ).hexdigest()
    chunks.append(TextChunk(
        chunk_id=chunk_id,
        text=text,
        metadata={
            "source": "web_portal",
            "url": page.url,
            "title": page.title,
            "service_type": page.service_type,
            "procedure_id": PROCEDURE_IDS_BY_DIR.get(page.service_type, page.service_type),
            "section": "web_content",
            "language": "multilingual",
            "source_type": "web_portal",
            "label_ar": page.label_ar,
            "source_key": page.source_key,
            "node_type": "web_chunk",
        },
    ))


# ─── Step 3: ChromaDB Upsert ──────────────────────────────────────────────────

def load_embedding_model():
    """Load BAAI/bge-m3 — the same model used by the RAG engine."""
    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        print("[INFO] Loading BAAI/bge-m3 embedding model (may take a moment)...")
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
        print("[OK] Embedding model loaded.")
        return embed_model
    except ImportError:
        raise ImportError(
            "llama-index-embeddings-huggingface is not installed. "
            "Run: pip install llama-index-embeddings-huggingface"
        )


def get_chroma_collection():
    """Return (client, collection) for the shared ChromaDB collection."""
    try:
        import chromadb
    except ImportError:
        raise ImportError("chromadb not installed. Run: pip install chromadb")

    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_model": "BAAI/bge-m3"},
    )
    return client, collection


def get_already_indexed_urls(collection) -> set[str]:
    """Return the set of URLs that have already been ingested into ChromaDB."""
    try:
        results = collection.get(include=["metadatas"])
        indexed = set()
        for meta in (results.get("metadatas") or []):
            if meta and meta.get("source") == "web_portal" and "url" in meta:
                indexed.add(meta["url"])
        return indexed
    except Exception:
        return set()


def upsert_chunks(chunks: list[TextChunk], collection, embed_model, batch_size: int = 32) -> int:
    """Embed and upsert chunks into ChromaDB. Returns the number upserted."""
    if not chunks:
        return 0

    ids, texts, metadatas, embeddings = [], [], [], []
    upserted = 0

    for i, chunk in enumerate(chunks):
        try:
            embedding = embed_model.get_text_embedding(chunk.text)
        except Exception as exc:
            print(f"  [WARN] Embedding failed for chunk {chunk.chunk_id}: {exc}")
            continue

        ids.append(chunk.chunk_id)
        texts.append(chunk.text)
        metadatas.append(chunk.metadata)
        embeddings.append(embedding)

        # Flush batch
        if len(ids) >= batch_size or i == len(chunks) - 1:
            if ids:
                try:
                    collection.upsert(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas,
                        embeddings=embeddings,
                    )
                    upserted += len(ids)
                    print(f"  [OK] Upserted batch of {len(ids)} chunks.")
                except Exception as exc:
                    print(f"  [ERROR] ChromaDB upsert failed: {exc}")
                ids, texts, metadatas, embeddings = [], [], [], []

    return upserted


# ─── Stats Command ────────────────────────────────────────────────────────────

def show_stats(collection) -> None:
    """Print a summary of what is currently in the ChromaDB collection."""
    total = collection.count()
    print(f"\n{'='*55}")
    print(f"  Collection : {COLLECTION_NAME}")
    print(f"  ChromaDB   : {CHROMA_DIR}")
    print(f"  Total docs : {total}")

    try:
        results = collection.get(include=["metadatas"])
        metas = results.get("metadatas") or []
        web_chunks = [m for m in metas if m and m.get("source") == "web_portal"]
        json_chunks = [m for m in metas if m and m.get("source") != "web_portal"]

        by_service: dict[str, int] = {}
        by_url: dict[str, int] = {}
        for m in web_chunks:
            svc = m.get("service_type", "unknown")
            url = m.get("url", "unknown")
            by_service[svc] = by_service.get(svc, 0) + 1
            by_url[url] = by_url.get(url, 0) + 1

        print(f"  Web chunks : {len(web_chunks)}")
        print(f"  JSON/MD    : {len(json_chunks)}")
        if by_service:
            print(f"\n  Web chunks by service:")
            for svc, count in sorted(by_service.items()):
                print(f"    {svc:<25} {count:>4} chunks")
        if by_url:
            print(f"\n  Indexed URLs ({len(by_url)}):")
            for url in sorted(by_url.keys()):
                print(f"    {url}")
    except Exception as exc:
        print(f"  [WARN] Could not retrieve metadata: {exc}")
    print(f"{'='*55}\n")


# ─── Bonus: Seed from existing JSON Knowledge Base ───────────────────────────

def seed_from_local_kb(collection, embed_model, force: bool = False) -> int:
    """Convert existing tests/knowledge_base/*.json files to ChromaDB vectors.

    This is the primary recommended mode for Ayoub (Ollama / offline setup).
    Uses the same BAAI/bge-m3 embeddings as the RAG engine.

    Already-indexed chunks are skipped unless --force is set.
    Returns the total number of chunks upserted.
    """
    import json

    kb_dir = _PROJECT_ROOT / "tests" / "knowledge_base"
    if not kb_dir.exists():
        print(f"[ERROR] Knowledge base directory not found: {kb_dir}")
        return 0

    # Check which chunk IDs are already in ChromaDB
    existing_ids: set[str] = set()
    if not force:
        try:
            results = collection.get(include=[])
            existing_ids = set(results.get("ids") or [])
        except Exception:
            existing_ids = set()

    all_chunks: list[TextChunk] = []
    excluded = {"test_cases.json", "all_test_cases.json"}

    for path in sorted(kb_dir.rglob("*.json")):
        if path.name in excluded or "test_cases" in str(path):
            continue

        relative = path.relative_to(kb_dir)
        service_type = relative.parts[0] if len(relative.parts) > 1 else "common"

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"  [WARN] Could not parse {path.name}: {exc}")
            continue

        svc_name = data.get("service_name_ar", service_type)
        source_url = f"kb://{service_type}/{path.name}"

        def _make_kb_chunk(text: str, node_type: str) -> None:
            if not text or len(text.strip()) < 20:
                return
            chunk_id = "kb_" + hashlib.md5(
                (source_url + text[:200]).encode("utf-8")
            ).hexdigest()
            if chunk_id in existing_ids:
                return  # already indexed
            all_chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=text.strip(),
                metadata={
                    "source": "local_kb",
                    "url": source_url,
                    "title": svc_name,
                    "service_type": service_type,
                    "procedure_id": PROCEDURE_IDS_BY_DIR.get(service_type, service_type),
                    "section": node_type,
                    "language": "ar",
                    "source_type": "official",
                    "label_ar": svc_name,
                    "source_key": service_type,
                    "node_type": node_type,
                    "file_name": path.name,
                },
            ))

        # FAQ entries (one chunk per Q&A pair)
        for faq in data.get("faq", []):
            q = faq.get("question", "")
            a = faq.get("answer", "")
            if q and a:
                _make_kb_chunk(f"سؤال: {q}\nجواب: {a}", "faq")

        # Scalar fields
        for field_key in ("description", "fees", "validity_period", "note"):
            val = data.get(field_key)
            if val and isinstance(val, str):
                _make_kb_chunk(f"{svc_name} - {field_key}: {val}", field_key)

        # Required documents
        req_docs = data.get("required_documents")
        if isinstance(req_docs, list) and req_docs:
            docs_text = "\n".join(f"- {d}" for d in req_docs)
            _make_kb_chunk(f"الوثائق المطلوبة لـ{svc_name}:\n{docs_text}", "required_documents")
        elif isinstance(req_docs, dict):
            for cat, doc_list in req_docs.items():
                if isinstance(doc_list, list) and doc_list:
                    docs_text = "\n".join(f"- {d}" for d in doc_list)
                    _make_kb_chunk(
                        f"الوثائق المطلوبة لـ{svc_name} ({cat}):\n{docs_text}",
                        "required_documents"
                    )

        # General steps
        steps = data.get("general_steps")
        if isinstance(steps, list) and steps:
            steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
            _make_kb_chunk(f"خطوات {svc_name}:\n{steps_text}", "general_steps")
        elif isinstance(steps, dict):
            for cat, step_list in steps.items():
                if isinstance(step_list, list) and step_list:
                    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(step_list))
                    _make_kb_chunk(f"خطوات {svc_name} ({cat}):\n{steps_text}", "general_steps")

        print(f"  [JSON] {path.name} -> {service_type} (queued {len(all_chunks)} total chunks so far)")

    if not all_chunks:
        print("[INFO] No new KB chunks to ingest (all already indexed or KB is empty).")
        return 0

    print(f"\n[INFO] Upserting {len(all_chunks)} KB chunks into ChromaDB...")
    return upsert_chunks(all_chunks, collection, embed_model)


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Moroccan portals and ingest content into ChromaDB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        help="Optional list of target keys to ingest (e.g. --targets residence birth). "
             "Omit to process ALL targets.",
        metavar="KEY",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and chunk content but do NOT write to ChromaDB.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest URLs that are already indexed (overwrite existing chunks).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show ChromaDB collection statistics and exit.",
    )
    parser.add_argument(
        "--seed-from-kb",
        action="store_true",
        help=(
            "Ingest the existing tests/knowledge_base/*.json files into ChromaDB. "
            "Recommended for Ollama / offline setups. "
            "Works without internet access."
        ),
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Maximum characters per chunk (default: 1000).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Character overlap between consecutive chunks (default: 200).",
    )
    args = parser.parse_args()

    # ── Stats mode ──────────────────────────────────────────────────────────
    if args.stats:
        _, collection = get_chroma_collection()
        show_stats(collection)
        return

    # ── Seed-from-KB mode (offline / Ollama) ────────────────────────────────
    if args.seed_from_kb:
        print(f"\n{'='*55}")
        print(f"  OmniAgent KB Seeding Pipeline (Local JSON -> ChromaDB)")
        print(f"  Force    : {args.force}")
        print(f"{'='*55}\n")
        _, collection = get_chroma_collection()
        embed_model = load_embedding_model()
        upserted = seed_from_local_kb(collection, embed_model, force=args.force)
        print(f"\n[OK] Seeding complete — {upserted} chunks upserted.")
        print(f"[INFO] Collection now has {collection.count()} total vectors.")
        show_stats(collection)
        return

    # ── Determine which targets to process ──────────────────────────────────
    if args.targets:
        keys_requested = set(args.targets)
        targets = [t for t in PORTAL_TARGETS if t["key"] in keys_requested]
        if not targets:
            print(
                f"[ERROR] No matching targets found for keys: {args.targets}\n"
                f"Available keys: {[t['key'] for t in PORTAL_TARGETS]}"
            )
            sys.exit(1)
    else:
        targets = PORTAL_TARGETS

    print(f"\n{'='*55}")
    print(f"  OmniAgent Web Ingestion Pipeline")
    print(f"  Targets  : {[t['key'] for t in targets]}")
    print(f"  Dry-run  : {args.dry_run}")
    print(f"  Force    : {args.force}")
    print(f"  Chunks   : size={args.chunk_size}, overlap={args.chunk_overlap}")
    print(f"{'='*55}\n")

    # ── Initialize ChromaDB + embedding model ────────────────────────────────
    if not args.dry_run:
        _, collection = get_chroma_collection()
        embed_model = load_embedding_model()
        already_indexed = get_already_indexed_urls(collection) if not args.force else set()
        print(f"[INFO] Collection '{COLLECTION_NAME}' has {collection.count()} existing vectors.")
        if already_indexed:
            print(f"[INFO] {len(already_indexed)} URL(s) already indexed (use --force to re-ingest).")
    else:
        collection = None
        embed_model = None
        already_indexed = set()

    # ── Process each target ──────────────────────────────────────────────────
    total_pages = 0
    total_chunks = 0
    total_upserted = 0

    for target in targets:
        print(f"\n[TARGET] {target['key']} — {target['label_ar']}")

        # Filter out already-indexed URLs unless --force
        urls_to_fetch = []
        for url in target["urls"]:
            if url in already_indexed:
                print(f"  [SKIP] Already indexed: {url}")
            else:
                urls_to_fetch.append(url)

        if not urls_to_fetch:
            print(f"  [SKIP] All URLs for '{target['key']}' are already indexed.")
            continue

        # Scrape
        target_copy = {**target, "urls": urls_to_fetch}
        pages = scrape_target(target_copy)
        total_pages += len(pages)

        # Chunk
        all_chunks: list[TextChunk] = []
        for page in pages:
            chunks = chunk_page(page, args.chunk_size, args.chunk_overlap)
            print(f"  Chunked '{page.title}' → {len(chunks)} chunks")
            all_chunks.extend(chunks)

        total_chunks += len(all_chunks)
        print(f"  Total chunks for '{target['key']}': {len(all_chunks)}")

        # Upsert
        if not args.dry_run and all_chunks:
            upserted = upsert_chunks(all_chunks, collection, embed_model)
            total_upserted += upserted
            print(f"  ✅ Upserted {upserted} chunks for '{target['key']}'")
        elif args.dry_run:
            print(f"  [DRY-RUN] Would upsert {len(all_chunks)} chunks.")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  Ingestion complete!")
    print(f"  Pages scraped  : {total_pages}")
    print(f"  Chunks created : {total_chunks}")
    if not args.dry_run:
        print(f"  Chunks upserted: {total_upserted}")
        _, collection = get_chroma_collection()
        print(f"  Collection total: {collection.count()} vectors")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
