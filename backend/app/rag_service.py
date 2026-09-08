"""RAG Service Module (OmniAgent RAG)

Wraps ChromaDB + LlamaIndex + BAAI/bge-m3 + configurable LLM into a reusable service.

Architecture upgrades:
  - Hybrid Search: Vector (ChromaDB) + BM25 keyword matching with Reciprocal Rank Fusion
  - Query Rewriting: Darija/French → formal MSA Arabic before search
  - Smart Service Detection: 50+ keywords across Darija/Arabic/French
  - Direct Answer Prompting: Forces concise, specific answers
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Optional, List, Dict, Sequence
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Resolve project paths
THIS_FILE = Path(__file__).resolve()
# Root directory of the project (omniagent-public-services-assistant)
ROOT_DIR = THIS_FILE.parents[2]
CHROMA_DIR = ROOT_DIR / "chroma_db"
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
EXCLUDED_KB_NAMES = {"test_cases.json", "all_test_cases.json"}

# ─── Improved QA Prompt (forces direct answers) ─────────────────────────────
QA_PROMPT_TMPL = (
    "المعلومات المتوفرة من الدليل الإداري الرسمي:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "أنت 'المساعد الذكي' للإجراءات والخدمات الإدارية العمومية بالمغرب.\n\n"
    "تعليمات صارمة للإجابة:\n"
    "1. أجب بدقة ومباشرة من المعلومات أعلاه فقط.\n"
    "2. إذا السؤال عن أجل أو مدة زمنية ← أعطي الرقم المحدد مباشرة "
    "(مثلا: '30 يوماً من تاريخ الوفاة').\n"
    "3. إذا السؤال عن الرسوم أو التكلفة ← أعطي المبلغ المحدد "
    "(مثلا: '10 دراهم').\n"
    "4. إذا السؤال عن الوثائق المطلوبة ← اذكر لائحة الوثائق بالنقاط.\n"
    "5. إذا السؤال عن المكان ← حدد المكان بالضبط.\n"
    "6. لا تعطي وصف عام للخدمة إذا كان السؤال محدد. "
    "أجب في 1-3 جمل إذا الجواب واضح.\n"
    "7. إذا السؤال بالفرنسية أجب بالفرنسية. "
    "إذا بالدارجة المغربية أجب بالدارجة. "
    "إذا بالعربية الفصحى أجب بالفصحى.\n"
    "8. فقط إذا كان السؤال خارجاً تماماً عن نطاق الخدمات الإدارية، "
    "قل: \"ما متأكدش من الجواب، هاد الموضوع خارج نطاق الخدمات الإدارية.\"\n\n"
    "السؤال: {query_str}\n"
    "الجواب المباشر: "
)

# ─── Query Rewrite Prompt (Darija/French → formal MSA) ───────────────────────
REWRITE_PROMPT = (
    "أنت مترجم متخصص. حول السؤال التالي إلى العربية الفصحى الرسمية "
    "مع الحفاظ على المعنى والقصد بالضبط.\n"
    "- إذا كان السؤال بالدارجة المغربية، ترجمه للفصحى.\n"
    "- إذا كان بالفرنسية، ترجمه للعربية الفصحى.\n"
    "- إذا كان بالفصحى أصلاً، أعده كما هو.\n"
    "- لا تضف أي شرح أو تعليق. فقط أعطي الترجمة.\n\n"
    "السؤال: {query}\n"
    "الترجمة بالعربية الفصحى: "
)

ConversationMessage = Dict[str, str]


# ─── Language Detection (fixes missing _detect_language bug) ─────────────────
def _detect_language(text: str) -> str:
    """Detect whether the text is Arabic (MSA), Darija, or French.

    Returns one of: 'arabic', 'darija', 'french'.
    """
    if not text or not text.strip():
        return "darija"

    # Count Latin vs Arabic characters
    latin_count = len(re.findall(
        r'[a-zA-ZàâçéèêëîïôûùüÿñæœÀÂÇÉÈÊËÎÏÔÛÙÜŸÑÆŒ]', text
    ))
    arabic_count = len(re.findall(
        r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text
    ))

    if latin_count > arabic_count:
        return "french"

    # Darija markers — common Darija words/slang not typically found in MSA
    darija_markers = [
        "شنو", "فين", "كيفاش", "واش", "علاش", "شحال", "باش", "ديال",
        "كاين", "ماشي", "بزاف", "دابا", "نقدر", "خاص", "غادي",
        "كتكلف", "نيلغ", "نخرج", "نروح", "نمشي", "هادي", "هاد",
        "كيتسنا", "كيخص", "كيدير", "بغيت", "عافاك", "عفاك",
    ]
    for marker in darija_markers:
        if marker in text:
            return "darija"

    if arabic_count > 0:
        return "arabic"

    return "darija"


# ─── Conversation History Formatting ─────────────────────────────────────────
def _format_conversation_history(
    history: Optional[Sequence[ConversationMessage]],
) -> str:
    """Render a small conversation window for context."""
    if not history:
        return ""
    labels = {"user": "المواطن", "assistant": "المساعد"}
    lines: List[str] = []
    # Take only the last 3 turns
    for item in history[-3:]:
        role = labels.get(item.get("role", ""), "المواطن")
        content = item.get("content", "").strip()
        if content and "ما متأكدش" not in content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _prompt_with_history(
    history: Optional[Sequence[ConversationMessage]],
) -> str:
    """Inject history into prompt cleanly if available."""
    history_text = _format_conversation_history(history)
    if history_text:
        return (
            "سياق المحادثة السابقة:\n"
            f"{history_text}\n"
            "---------------------\n"
            + QA_PROMPT_TMPL
        )
    return QA_PROMPT_TMPL


# ─── Rate Limit Detection ────────────────────────────────────────────────────
def _is_rate_limit_error(error: BaseException) -> bool:
    """Recognize HTTP 429 across provider SDK exception wrappers."""
    current: Optional[BaseException] = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        status = getattr(current, "status_code", None) or getattr(
            current, "code", None
        )
        text = str(current).lower()
        if (
            status == 429
            or "429" in text
            or "resource_exhausted" in text
            or "rate limit" in text
        ):
            return True
        current = current.__cause__ or current.__context__
    return False


# ─── Expanded Service Auto-Detection Keywords ────────────────────────────────
# Maps keywords (Arabic/Darija/French) → canonical service_id.
# Expanded with 50+ additional Darija slang, French partials, and synonyms.
_SERVICE_KEYWORDS: Dict[str, List[str]] = {
    "criminal_record": [
        "السجل العدلي", "سجل عدلي", "casier judiciaire", "criminal record",
        "الكازي", "كازي جوديسيار",
        # ── New expansions ──
        "كازي", "casier", "judiciaire",
        "بدون سوابق", "سوابق عدلية", "سوابق",
    ],
    "birth_certificate": [
        "عقد الازدياد", "رسم الولادة", "شهادة الميلاد", "acte de naissance",
        "عقد ازدياد", "الازدياد",
        # ── New expansions ──
        "مزيود", "الميلاد", "ولادة", "naissance",
        "watiqa", "واتيقة", "ازداد", "رسم ولادة",
    ],
    "residence_certificate": [
        "شهادة السكنى", "السكنى", "certificat de résidence", "شهادة سكنى",
        # ── New expansions ──
        "سكنى", "فين ساكن", "résidence", "habitation", "سكن",
        "إثبات السكن", "محل السكنى",
    ],
    "marriage_contract": [
        "عقد الزواج", "عقد زواج", "الزواج", "acte de mariage", "زواج",
        # ── New expansions ──
        "تزوج", "زوجة", "mariage", "نيشان", "خطوبة", "الصداق",
        "العدول", "عدول",
    ],
    "death_certificate": [
        "شهادة الوفاة", "رسم الوفاة", "الوفاة", "acte de décès",
        # ── New expansions ──
        "مات", "توفى", "décès", "mort", "التصريح بالوفاة",
        "وفاة", "مستخرج الوفاة", "التبليغ عن الوفاة",
        "نيلغ على الوفاة", "نبلغ على الوفاة",
    ],
    "life_certificate": [
        "شهادة الحياة", "الحياة", "certificat de vie",
        # ── New expansions ──
        "حي", "عايش", "vie", "vivant", "على قيد الحياة",
    ],
    "single_status_certificate": [
        "شهادة العزوبة", "العزوبة", "célibat",
        # ── New expansions ──
        "عازب", "ماشي متزوج", "célibataire", "مازال ما تزوجت",
        "عزوبة", "غير متزوج",
    ],
    "non_property_certificate": [
        "شهادة عدم الملكية", "عدم الملكية", "non propriété",
        # ── New expansions ──
        "ما عندي حتى ملك", "non propriétaire", "عقار",
    ],
    "administrative_certificate": [
        "الشهادة الإدارية", "شهادة إدارية", "certificat administratif",
        # ── New expansions ──
        "شهادة ادارية", "إدارية",
    ],
    "good_conduct_certificate": [
        "شهادة حسن السيرة", "حسن السيرة", "bonne conduite",
        # ── New expansions ──
        "سلوك", "السيرة", "bonne moralité", "حسن السلوك",
    ],
}


def _detect_service_from_query(user_query: str) -> Optional[str]:
    """Auto-detect the service type from keywords in the user's question."""
    query_lower = user_query.lower()
    for service_id, keywords in _SERVICE_KEYWORDS.items():
        for kw in keywords:
            if kw in user_query or kw.lower() in query_lower:
                return service_id
    return None


# ─── BM25 Node Loading ──────────────────────────────────────────────────────
def _load_kb_nodes() -> list:
    """Load knowledge base files into granular TextNode objects for BM25.

    Creates fine-grained nodes (one per FAQ entry, one per structured field)
    so BM25 keyword matching can pinpoint exact answers.
    """
    from llama_index.core.schema import TextNode

    nodes: list = []

    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
            continue
        if path.name in EXCLUDED_KB_NAMES or "test_cases.json" in path.parts:
            continue

        relative = path.relative_to(KNOWLEDGE_DIR)
        service_type = relative.parts[0] if len(relative.parts) > 1 else "common"
        base_meta = {
            "service_type": service_type,
            "file_name": path.name,
            "file_path": str(path),
        }

        # ── JSON Knowledge Files ──
        if path.suffix.lower() == ".json":
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                text = path.read_text(encoding="utf-8", errors="replace")
                nodes.append(TextNode(
                    text=text,
                    metadata={**base_meta, "node_type": "raw"},
                ))
                continue

            svc_name = data.get("service_name_ar", service_type)

            # One node per FAQ entry (granular — best for BM25)
            for faq in data.get("faq", []):
                q = faq.get("question", "")
                a = faq.get("answer", "")
                if q and a:
                    nodes.append(TextNode(
                        text=f"سؤال: {q}\nجواب: {a}",
                        metadata={**base_meta, "node_type": "faq"},
                    ))

            # One node per scalar field
            for field_key in ("description", "fees", "validity_period", "note"):
                value = data.get(field_key)
                if value and isinstance(value, str):
                    nodes.append(TextNode(
                        text=f"{svc_name} - {field_key}: {value}",
                        metadata={**base_meta, "node_type": field_key},
                    ))

            # Nodes from required_documents
            req_docs = data.get("required_documents")
            if isinstance(req_docs, list) and req_docs:
                docs_text = "\n".join(f"- {d}" for d in req_docs)
                nodes.append(TextNode(
                    text=f"الوثائق المطلوبة لـ{svc_name}:\n{docs_text}",
                    metadata={**base_meta, "node_type": "required_documents"},
                ))
            elif isinstance(req_docs, dict):
                for cat, doc_list in req_docs.items():
                    if isinstance(doc_list, list) and doc_list:
                        docs_text = "\n".join(f"- {d}" for d in doc_list)
                        nodes.append(TextNode(
                            text=f"الوثائق المطلوبة لـ{svc_name} ({cat}):\n{docs_text}",
                            metadata={**base_meta, "node_type": "required_documents"},
                        ))

            # Nodes from general_steps
            steps = data.get("general_steps")
            if isinstance(steps, list) and steps:
                steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
                nodes.append(TextNode(
                    text=f"خطوات {svc_name}:\n{steps_text}",
                    metadata={**base_meta, "node_type": "general_steps"},
                ))
            elif isinstance(steps, dict):
                for cat, step_list in steps.items():
                    if isinstance(step_list, list) and step_list:
                        steps_text = "\n".join(
                            f"{i+1}. {s}" for i, s in enumerate(step_list)
                        )
                        nodes.append(TextNode(
                            text=f"خطوات {svc_name} ({cat}):\n{steps_text}",
                            metadata={**base_meta, "node_type": "general_steps"},
                        ))

        # ── Markdown Files ──
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                nodes.append(TextNode(
                    text=text,
                    metadata={**base_meta, "node_type": "markdown"},
                ))

    return nodes


# ─── Reciprocal Rank Fusion ─────────────────────────────────────────────────
def _reciprocal_rank_fusion(
    results_lists: List[list],
    k: int = 60,
    top_n: int = 5,
) -> list:
    """Combine results from multiple retrievers using Reciprocal Rank Fusion.

    Each result list is a List[NodeWithScore]. Nodes appearing in multiple
    lists get a higher fused score. Deduplication by text prefix.

    Args:
        results_lists: List of retriever result lists.
        k: RRF constant (default 60, standard in literature).
        top_n: Number of results to return.
    """
    # Accumulate RRF scores keyed by a text fingerprint (first 120 chars)
    fused_scores: Dict[str, float] = {}
    node_map: Dict[str, Any] = {}  # fingerprint → best NodeWithScore

    for results in results_lists:
        for rank, node_with_score in enumerate(results):
            text = getattr(node_with_score.node, "text", "") or ""
            fingerprint = text[:120].strip()
            if not fingerprint:
                continue

            rrf_score = 1.0 / (k + rank + 1)
            fused_scores[fingerprint] = (
                fused_scores.get(fingerprint, 0.0) + rrf_score
            )

            # Keep the copy with the higher original score
            existing = node_map.get(fingerprint)
            if existing is None:
                node_map[fingerprint] = node_with_score
            else:
                old_score = getattr(existing, "score", 0.0) or 0.0
                new_score = getattr(node_with_score, "score", 0.0) or 0.0
                if new_score > old_score:
                    node_map[fingerprint] = node_with_score

    # Sort by fused score descending
    sorted_fps = sorted(
        fused_scores.keys(), key=lambda fp: fused_scores[fp], reverse=True
    )

    from llama_index.core.schema import NodeWithScore

    return [
        NodeWithScore(node=node_map[fp].node, score=fused_scores[fp])
        for fp in sorted_fps[:top_n]
        if fp in node_map
    ]


# ─── Arabic Tokenizer for BM25 ──────────────────────────────────────────────
def _tokenize_arabic(text: str) -> List[str]:
    """Tokenize Arabic/Darija/French text for BM25 indexing.

    Splits on whitespace and punctuation, lowercases Latin chars,
    and removes very short tokens.
    """
    # Split on whitespace and common punctuation
    tokens = re.findall(r"[\w\u0600-\u06FF\u0750-\u077F]+", text, re.UNICODE)
    return [t.lower() if t.isascii() else t for t in tokens if len(t) > 1]


# ─── Normalise service_type → metadata folder name ──────────────────────────
def _normalize_service_filter(service_type: str) -> str:
    """Convert canonical service id (e.g. 'death_certificate') to the
    folder name stored in ChromaDB metadata (e.g. 'death')."""
    return (
        service_type.lower()
        .replace("_certificate", "")
        .replace("_contract", "")
        .strip()
    )


# ═════════════════════════════════════════════════════════════════════════════
# Main RAG Engine
# ═════════════════════════════════════════════════════════════════════════════
class OmniAgentRAG:
    """Reusable RAG engine with hybrid retrieval and query rewriting."""

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        collection_name: str = "public_services_kb",
        ollama_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.chroma_dir = chroma_dir or CHROMA_DIR
        self.collection_name = collection_name
        self.initialized = False
        self.index = None
        self.qa_prompt = None
        self.bm25_retriever = None  # NEW: BM25 retriever for hybrid search
        self._rewrite_cache: Dict[str, str] = {}  # query → MSA cache
        self._model_overrides = {
            key: value
            for key, value in {
                "ollama_model": ollama_model,
                "gemini_model": gemini_model,
            }.items()
            if value is not None
        }
        self._init_rag()

    # ─── Initialization ──────────────────────────────────────────────────
    def _init_rag(self) -> None:
        """Initialize LlamaIndex, ChromaDB vector store, and BM25 retriever."""
        try:
            os.environ["ANONYMIZED_TELEMETRY"] = "False"

            import chromadb
            from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            from app.core.config import settings as app_settings
            from app.llm_factory import create_llm

            # Only generation varies; retrieval and embeddings remain shared.
            llm_settings = app_settings.model_copy(update=self._model_overrides)
            Settings.llm = create_llm(llm_settings)

            # Embeddings using BAAI/bge-m3 (multilingual, strong Arabic)
            Settings.embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-m3"
            )

            # ── ChromaDB Vector Store ──
            if self.chroma_dir.exists():
                client = chromadb.PersistentClient(path=str(self.chroma_dir))
                collection = client.get_or_create_collection(self.collection_name)
                vector_store = ChromaVectorStore(chroma_collection=collection)
                self.index = VectorStoreIndex.from_vector_store(vector_store)
                self.qa_prompt = PromptTemplate(QA_PROMPT_TMPL)
                self.initialized = True
                print(
                    f"[OK] OmniAgentRAG initialized: collection "
                    f"'{collection.name}' ({collection.count()} vectors)."
                )
            else:
                print(
                    f"[WARN] ChromaDB directory not found at "
                    f"{self.chroma_dir}. RAG running in fallback mode."
                )
                self.initialized = False

            # ── BM25 Retriever (Hybrid Search) ──
            try:
                from rank_bm25 import BM25Okapi

                kb_nodes = _load_kb_nodes()
                if kb_nodes:
                    self._bm25_nodes = kb_nodes
                    # Tokenize each node's text for BM25 indexing
                    corpus = [
                        _tokenize_arabic(node.text) for node in kb_nodes
                    ]
                    self._bm25_index = BM25Okapi(corpus)
                    self.bm25_retriever = True  # flag that BM25 is available
                    print(
                        f"[OK] BM25 retriever initialized with "
                        f"{len(kb_nodes)} nodes from knowledge base."
                    )
                else:
                    print("[WARN] No KB nodes found for BM25 retriever.")
            except ImportError:
                print(
                    "[WARN] rank-bm25 not installed. "
                    "Hybrid search disabled; using vector-only retrieval."
                )
            except Exception as bm25_err:
                print(f"[WARN] BM25 initialization failed: {bm25_err}")

        except Exception as e:
            provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
            print(
                f"[WARN] LLM provider '{provider}' unavailable "
                f"during RAG initialization: {e}"
            )
            self.initialized = False

    # ─── Query Rewriting (Darija/French → MSA) ───────────────────────────
    def _rewrite_query(self, user_query: str) -> str:
        """Rewrite Darija/French query to formal Arabic for better retrieval.

        Uses the configured LLM (Gemini Flash) to normalize the query.
        Returns the original query on failure.
        """
        lang = _detect_language(user_query)
        if lang == "arabic":
            return user_query  # Already formal Arabic

        # Check cache
        if user_query in self._rewrite_cache:
            return self._rewrite_cache[user_query]

        try:
            from llama_index.core import Settings as LISettings

            prompt = REWRITE_PROMPT.replace("{query}", user_query)
            response = LISettings.llm.complete(prompt)
            rewritten = str(response).strip()

            # Sanity check — rewritten should contain Arabic characters
            if re.search(r"[\u0600-\u06FF]", rewritten) and len(rewritten) > 3:
                # Remove any preamble the LLM might add
                # (sometimes it says "الترجمة: ..." before the actual text)
                for prefix in ["الترجمة:", "الترجمة بالعربية الفصحى:"]:
                    if rewritten.startswith(prefix):
                        rewritten = rewritten[len(prefix):].strip()

                self._rewrite_cache[user_query] = rewritten
                print(
                    f"[REWRITE] '{user_query[:50]}' → "
                    f"'{rewritten[:50]}'"
                )
                return rewritten
            else:
                return user_query
        except Exception as e:
            print(f"[WARN] Query rewrite failed: {e}")
            return user_query

    # ─── Main Query Method ───────────────────────────────────────────────
    def query(
        self,
        user_query: str,
        service_type: Optional[str] = None,
        conversation_history: Optional[Sequence[ConversationMessage]] = None,
    ) -> Dict[str, Any]:
        """Query RAG pipeline with hybrid search and query rewriting.

        Flow:
          1. Detect language → auto-detect service type
          2. Rewrite query (Darija/French → MSA) for better retrieval
          3. Vector search (ChromaDB) with rewritten query + metadata filter
          4. BM25 keyword search with original query + post-filter
          5. Fuse results using Reciprocal Rank Fusion
          6. Generate answer with the improved direct-answer prompt

        Args:
            user_query: The question in Arabic, Darija, or French.
            service_type: Optional service category filter.
            conversation_history: Optional recent conversation turns.

        Returns:
            Dict with 'answer', 'sources', 'confidence', and 'language'.
        """
        if not self.initialized or self.index is None:
            return self._fallback_query(
                user_query, service_type, reason="RAG Vector Index offline"
            )

        # Step 1: Detect language and auto-detect service
        detected_lang = _detect_language(user_query)
        resolved_service = service_type or _detect_service_from_query(user_query)

        try:
            # Step 2: Rewrite query to MSA for better retrieval
            rewritten_query = self._rewrite_query(user_query)

            # Step 3: Build metadata filter for service type
            filters = None
            clean_service = None
            if resolved_service:
                clean_service = _normalize_service_filter(resolved_service)
                from llama_index.core.vector_stores import (
                    MetadataFilters,
                    ExactMatchFilter,
                )
                filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(
                            key="service_type", value=clean_service
                        )
                    ]
                )

            # Step 4: Vector retrieval with rewritten query
            vector_retriever = self.index.as_retriever(
                similarity_top_k=5,
                filters=filters,
            )
            vector_nodes = vector_retriever.retrieve(rewritten_query)

            # Step 5: BM25 retrieval with original query (keyword matching)
            bm25_nodes: list = []
            if self.bm25_retriever and hasattr(self, "_bm25_index"):
                try:
                    from llama_index.core.schema import NodeWithScore

                    query_tokens = _tokenize_arabic(user_query)
                    scores = self._bm25_index.get_scores(query_tokens)

                    # Get top-10 indices by BM25 score
                    import numpy as np

                    top_indices = np.argsort(scores)[::-1][:10]

                    raw_bm25 = []
                    for idx in top_indices:
                        if scores[idx] > 0:
                            raw_bm25.append(
                                NodeWithScore(
                                    node=self._bm25_nodes[idx],
                                    score=float(scores[idx]),
                                )
                            )

                    if clean_service:
                        # Post-filter BM25 results by service type
                        bm25_nodes = [
                            n
                            for n in raw_bm25
                            if n.node.metadata.get("service_type", "")
                            == clean_service
                        ]
                        # If too few matches after filter, keep unfiltered
                        if len(bm25_nodes) < 2:
                            bm25_nodes = raw_bm25[:5]
                    else:
                        bm25_nodes = raw_bm25[:5]
                except Exception as bm25_err:
                    print(f"[WARN] BM25 retrieval failed: {bm25_err}")

            # Step 6: Reciprocal Rank Fusion
            combined = _reciprocal_rank_fusion(
                [vector_nodes, bm25_nodes], top_n=5
            )

            # Step 7: Build context from fused nodes
            context_parts = [
                node.node.text
                for node in combined
                if getattr(node.node, "text", "").strip()
            ]
            context = "\n\n---\n\n".join(context_parts)

            if not context.strip():
                return self._fallback_query(
                    user_query,
                    service_type,
                    reason="No relevant context found after hybrid search",
                )

            # Step 8: Format prompt with conversation history
            prompt_tmpl = _prompt_with_history(conversation_history)
            prompt = prompt_tmpl.replace(
                "{context_str}", context
            ).replace("{query_str}", user_query)

            # Step 9: Call LLM to generate answer
            from llama_index.core import Settings as LISettings

            response = LISettings.llm.complete(prompt)
            answer_text = str(response).strip()

            # Step 10: Extract metadata from retrieved nodes
            sources: List[str] = []
            max_score = 0.0

            for node_with_score in combined:
                meta = getattr(node_with_score.node, "metadata", {}) or {}
                score = getattr(node_with_score, "score", 0.0) or 0.0
                if score > max_score:
                    max_score = float(score)

                fp = meta.get("file_path", "") or meta.get("file_name", "")
                if fp:
                    rel_path = Path(fp).name
                    if rel_path not in sources:
                        sources.append(rel_path)

            # Calculate confidence — RRF scores are inherently small
            # (max ~0.033), so we normalize: base 0.80 for any RAG answer,
            # boosted by the number of retrieval sources and result count.
            n_results = len(combined)
            n_bm25_hits = len(bm25_nodes)
            if n_results > 0:
                base = 0.80
                # Boost if multiple sources found
                source_boost = min(0.10, 0.02 * len(sources))
                # Boost if BM25 also found matches (hybrid agreement)
                bm25_boost = 0.05 if n_bm25_hits > 0 else 0.0
                confidence = round(
                    min(0.98, base + source_boost + bm25_boost), 2
                )
            else:
                confidence = 0.50

            uncertainty_markers = [
                "ما متأكدش",
                "لست متأكداً",
                "Je ne suis pas sûr",
            ]
            if any(marker in answer_text for marker in uncertainty_markers):
                confidence = 0.30

            return {
                "answer": answer_text,
                "sources": (
                    sources
                    if sources
                    else [resolved_service or "knowledge_base"]
                ),
                "confidence": confidence,
                "language": detected_lang,
            }

        except Exception as e:
            provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
            if _is_rate_limit_error(e):
                print(
                    f"[WARN] LLM provider '{provider}' rate limited "
                    f"(HTTP 429); using local KB fallback"
                )
                return self._fallback_query(
                    user_query,
                    service_type,
                    reason=f"LLM provider '{provider}' rate limited (HTTP 429)",
                )
            print(
                f"[WARN] LLM provider '{provider}' unavailable "
                f"during RAG query: {e}"
            )
            return self._fallback_query(
                user_query, service_type, reason=str(e)
            )

    # ─── Fallback to Structured KB ───────────────────────────────────────
    def _fallback_query(
        self,
        user_query: str,
        service_type: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        """Fallback to local structured Knowledge Base if RAG is unavailable."""
        try:
            from app.services.knowledge_base import answer_with_metadata

            # Auto-detect service type from the question if not provided
            resolved_service = (
                service_type
                or _detect_service_from_query(user_query)
            )

            # If no service detected at all, return a generic "I need more info" response
            if not resolved_service:
                return {
                    "answer": (
                        "ما قدرتش نفهم بالضبط شنو كتحتاج. "
                        "تقدر تعطيني مزيد من التفاصيل؟\n\n"
                        "مثلاً: شهادة السكنى، عقد الازدياد، CIN، السجل العدلي..."
                    ),
                    "sources": [],
                    "confidence": 0.0,
                    "language": "darija",
                    "fallback_reason": reason,
                }

            kb_ans = answer_with_metadata(
                resolved_service, user_query, use_rag=False
            )
            return {
                "answer": kb_ans.answer,
                "sources": kb_ans.sources,
                "confidence": kb_ans.confidence,
                "language": "darija",
                "fallback_reason": reason,
            }
        except Exception as fallback_err:
            return {
                "answer": "المعلومات غير متوفرة حاليا، يرجى المحاولة لاحقا.",
                "sources": [],
                "confidence": 0.0,
                "language": "darija",
                "fallback_reason": (
                    f"{reason}; Fallback error: {fallback_err}"
                ),
            }


# ═════════════════════════════════════════════════════════════════════════════
# Global Singleton
# ═════════════════════════════════════════════════════════════════════════════
_rag_instance: Optional[OmniAgentRAG] = None


def get_rag_engine() -> OmniAgentRAG:
    """Get or create singleton instance of OmniAgentRAG."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = OmniAgentRAG()
    return _rag_instance


def query_rag(
    user_query: str,
    service_type: Optional[str] = None,
    conversation_history: Optional[Sequence[ConversationMessage]] = None,
) -> Dict[str, Any]:
    """Public functional interface for querying the RAG pipeline.

    Args:
        user_query: User question in Darija/Arabic/French.
        service_type: Optional category filter.
        conversation_history: Optional recent conversation turns.

    Returns:
        Dict: {"answer": "...", "sources": [...], "confidence": 0.92, "language": "darija"}
    """
    engine = get_rag_engine()
    return engine.query(
        user_query=user_query,
        service_type=service_type,
        conversation_history=conversation_history,
    )
