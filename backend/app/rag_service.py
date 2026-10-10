"""RAG Service Module (OmniAgent RAG).

BM25 default, or explicitly configured Chroma cosine/BGE-M3 retrieval.
The optional vector runtime needs more memory than the lightweight deployment.

Architecture:
  - BM25 keyword search over local knowledge base JSON/MD files
  - Query Rewriting: Darija/French -> formal MSA Arabic before search
  - Smart Service Detection: 50+ keywords across Darija/Arabic/French
  - Direct Answer Prompting via Gemini Flash
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, List, Dict, Sequence

from dotenv import load_dotenv

from app.services.gemini_client import GeminiRequestError, generate_text
from app.services.procedure_schema import (
    build_retrieval_query,
    detect_explicit_procedure,
    detect_section,
    generate_procedure_chunks,
    iter_normalized_procedures,
    load_normalized_procedure,
    procedure_path,
)

# Resolve project paths
THIS_FILE = Path(__file__).resolve()
# Root directory of the project (omniagent-public-services-assistant)
ROOT_DIR = THIS_FILE.parents[2]
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
EXCLUDED_KB_NAMES = {"test_cases.json", "all_test_cases.json"}
CHROMA_DIR = ROOT_DIR / "chroma_db"
CHROMA_COLLECTION = "public_services_kb"
logger = logging.getLogger(__name__)

# Load environment variables from .env if present (root and backend)
load_dotenv(ROOT_DIR / ".env")
load_dotenv(THIS_FILE.parents[1] / ".env")


# ─── Lightweight data classes (replace LlamaIndex TextNode / NodeWithScore) ──
@dataclass
class KBNode:
    """A single knowledge-base chunk with metadata."""
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredNode:
    """A KBNode with a relevance score."""
    node: KBNode = field(default_factory=KBNode)
    score: float = 0.0


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

# ─── Query Rewrite Prompt (Darija/French -> formal MSA) ───────────────────────
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
    labels = {"user": "User", "assistant": "Assistant"}
    lines: List[str] = []
    # Five exchanges are enough for generation continuity. Retrieval itself
    # intentionally uses only the current message plus resolved procedure.
    for item in history[-10:]:
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
# Maps keywords (Arabic/Darija/French) -> canonical service_id.
# Expanded with 50+ additional Darija slang, French partials, and synonyms.
_SERVICE_KEYWORDS: Dict[str, List[str]] = {
    "identity_card": [
        "بطاقة التعريف الوطنية", "البطاقة الوطنية", "بطاقة التعريف",
        "تجديد البطاقة", "لاكارط ناسيونال", "لاكارت ناسيونال",
        "carte nationale d'identité", "carte nationale d’identité",
        "carte d'identité", "carte d’identité", "cnie", "cin",
        "national identity card", "identity card",
    ],
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
    configured = detect_explicit_procedure(user_query)
    if configured:
        return configured
    query_lower = user_query.lower()
    for service_id, keywords in _SERVICE_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"(?<!\w)" + re.escape(kw.lower()) + r"(?!\w)", query_lower):
                return service_id
    return None


# ─── BM25 Node Loading ──────────────────────────────────────────────────────
def _load_kb_nodes() -> List[KBNode]:
    """Load the same normalized section chunks used by Chroma into BM25."""
    return [
        KBNode(text=chunk.text, metadata=dict(chunk.metadata))
        for procedure, path in iter_normalized_procedures()
        for chunk in generate_procedure_chunks(procedure, path)
    ]


# ─── Arabic Tokenizer for BM25 ──────────────────────────────────────────────
def _tokenize_arabic(text: str) -> List[str]:
    """Tokenize Arabic/Darija/French text for BM25 indexing.

    Splits on whitespace and punctuation, lowercases Latin chars,
    and removes very short tokens.
    """
    # Unicode word characters without underscore; unlike the previous broad
    # Arabic block range this excludes Arabic punctuation such as "؟" and "،".
    tokens = re.findall(r"[^\W_]+", text, re.UNICODE)
    return [t.lower() if t.isascii() else t for t in tokens if len(t) > 1]


# ─── Normalise service_type -> metadata folder name ──────────────────────────
def _normalize_service_filter(service_type: str) -> str:
    """Convert canonical service id (e.g. 'death_certificate') to the
    folder name stored in metadata (e.g. 'death')."""
    return (
        service_type.lower()
        .replace("_certificate", "")
        .replace("_contract", "")
        .strip()
    )


# ─── Gemini LLM wrapper ─────────────────────────────────────────────────────
def _create_gemini_model():
    """Return the current-SDK Gemini configuration.

    Returns None if GOOGLE_API_KEY is missing.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    if not api_key:
        print("[WARN] GOOGLE_API_KEY not set -- LLM features disabled")
        return None

    print(f"[OK] Gemini model configured: {model_name}")
    return api_key, model_name


def _llm_generate(
    model_config,
    prompt: str,
    diagnostics: Optional[Dict[str, str]] = None,
) -> str:
    """Call Gemini generate_content and return text. Returns '' on failure."""
    if model_config is None:
        if diagnostics is not None:
            diagnostics.update(status="fallback", fallback_reason="gemini_not_configured")
        return ""
    api_key, model_name = model_config
    try:
        result = generate_text(
            api_key=api_key,
            model=model_name,
            contents=prompt,
            temperature=0.1,
        )
        if diagnostics is not None:
            if result:
                diagnostics.update(status="success")
                diagnostics.pop("fallback_reason", None)
            else:
                diagnostics.update(status="fallback", fallback_reason="gemini_empty_response")
        return result
    except GeminiRequestError as exc:
        reason = getattr(exc, "reason", "gemini_request_failed")
        if reason == "gemini_request_failed" and _is_rate_limit_error(exc):
            reason = "gemini_rate_limited_http_429"
        if diagnostics is not None:
            diagnostics.update(status="fallback", fallback_reason=reason)
        return ""


# ═════════════════════════════════════════════════════════════════════════════
# Main RAG Engine
# ═════════════════════════════════════════════════════════════════════════════
class OmniAgentRAG:
    """Procedure-aware Chroma/BGE-M3 RAG with a local BM25 fallback."""

    def __init__(
        self,
        ollama_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.initialized = False
        self.vector_retriever = False
        self.bm25_retriever = False
        self._gemini = None
        self._chroma_client = None
        self._chroma_collection = None
        self._embedding_model = None
        self._bm25_nodes: List[KBNode] = []
        self._bm25_index = None
        self._rewrite_cache: Dict[str, str] = {}
        self._vector = None
        self._vector_error = None
        self.backend = os.getenv("RAG_BACKEND", "bm25").lower()
        if self.backend not in {"bm25", "chroma"}:
            raise ValueError("RAG_BACKEND must be bm25 or chroma")
        # Allow overriding model name
        if gemini_model:
            os.environ["GEMINI_MODEL"] = gemini_model
        self._init_rag()

    # ─── Initialization ──────────────────────────────────────────────────
    def _init_rag(self) -> None:
        """Initialize Chroma metadata, BM25 fallback, and Gemini."""
        try:
            # ── 1. Gemini LLM ──
            self._gemini = _create_gemini_model()
            if self.backend == "chroma":
                from app.services.vector_retrieval import VectorRetriever
                try:
                    self._vector = VectorRetriever.from_environment()
                    self.initialized = True
                except Exception as exc:
                    self._vector_error = str(exc)
                    print(f"[WARN] Vector retrieval unavailable: {exc}")
                return

            # ── 2. Chroma collection (BGE-M3 model loads lazily) ──
            try:
                import chromadb

                if CHROMA_DIR.exists():
                    self._chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
                    self._chroma_collection = self._chroma_client.get_collection(CHROMA_COLLECTION)
                    if self._chroma_collection.count() > 0:
                        self.vector_retriever = True
                        self.initialized = True
                        print(f"[OK] Chroma retriever ready: {CHROMA_COLLECTION} ({self._chroma_collection.count()} chunks).")
            except Exception as chroma_err:
                print(f"[WARN] Chroma unavailable; BM25 fallback remains active: {chroma_err}")

            # ── 3. BM25 fallback (also useful in constrained deployments) ──
            try:
                from rank_bm25 import BM25Okapi

                kb_nodes = _load_kb_nodes()
                if kb_nodes:
                    self._bm25_nodes = kb_nodes
                    corpus = [_tokenize_arabic(node.text) for node in kb_nodes]
                    self._bm25_index = BM25Okapi(corpus)
                    self.bm25_retriever = True
                    self.initialized = True
                    print(f"[OK] BM25 retriever initialized with {len(kb_nodes)} nodes from knowledge base.")
                else:
                    print("[WARN] No KB nodes found for BM25 retriever.")
            except Exception as bm25_err:
                print(f"[WARN] BM25 initialization failed: {bm25_err}")

        except Exception as e:
            print(f"[WARN] RAG initialization error: {e}")
            self.initialized = False

    def _retrieve_chroma(
        self,
        retrieval_query: str,
        procedure_id: str | None,
        section: str | None,
        limit: int = 8,
    ) -> List[ScoredNode]:
        """Retrieve with a strict procedure filter and a soft section boost."""
        if not getattr(self, "vector_retriever", False) or getattr(self, "_chroma_collection", None) is None:
            return []
        try:
            if self._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                from huggingface_hub import snapshot_download

                model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
                # Retrieval must not make a network request on every process
                # start. Deployments without the cached model fall back to
                # BM25 until the documented index/model setup is completed.
                local_model_path = snapshot_download(
                    repo_id=model_name,
                    local_files_only=True,
                )
                self._embedding_model = SentenceTransformer(local_model_path, local_files_only=True)
            embedding = self._embedding_model.encode(
                [retrieval_query], normalize_embeddings=True, show_progress_bar=False
            )[0].tolist()
            kwargs: Dict[str, Any] = {
                "query_embeddings": [embedding],
                "n_results": limit,
                "include": ["documents", "metadatas", "distances"],
            }
            if procedure_id:
                kwargs["where"] = {"procedure_id": procedure_id}
            result = self._chroma_collection.query(**kwargs)
            documents = (result.get("documents") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            ranked: list[tuple[float, ScoredNode]] = []
            for document, metadata, distance in zip(documents, metadatas, distances):
                meta = dict(metadata or {})
                similarity = max(-1.0, min(1.0, 1.0 - float(distance)))
                preference = 0.08 if section and meta.get("section") == section else 0.0
                ranked.append((similarity + preference, ScoredNode(KBNode(document or "", meta), similarity)))
            ranked.sort(key=lambda item: item[0], reverse=True)
            return [item[1] for item in ranked[:5]]
        except Exception as error:
            logger.warning("[RAG] Chroma retrieval failed; using BM25 fallback: %s", error)
            return []

    # ─── Query Rewriting (Darija/French -> MSA) ───────────────────────────
    def _rewrite_query(
        self,
        user_query: str,
        diagnostics: Optional[Dict[str, str]] = None,
    ) -> str:
        """Rewrite Darija/French query to formal Arabic for better retrieval.

        Uses the configured LLM (Gemini Flash) to normalize the query.
        Returns the original query on failure.
        """
        lang = _detect_language(user_query)
        if lang == "arabic":
            return user_query  # Already formal Arabic

        # Check cache
        rewrite_cache = getattr(self, "_rewrite_cache", None)
        if rewrite_cache is None:
            rewrite_cache = self._rewrite_cache = {}
        if user_query in rewrite_cache:
            return rewrite_cache[user_query]

        try:
            prompt = REWRITE_PROMPT.replace("{query}", user_query)
            rewritten = _llm_generate(self._gemini, prompt, diagnostics)

            # Sanity check -- rewritten should contain Arabic characters
            if re.search(r"[\u0600-\u06FF]", rewritten) and len(rewritten) > 3:
                # Remove any preamble the LLM might add
                for prefix in ["الترجمة:", "الترجمة بالعربية الفصحى:"]:
                    if rewritten.startswith(prefix):
                        rewritten = rewritten[len(prefix):].strip()

                rewrite_cache[user_query] = rewritten
                return rewritten
            else:
                return user_query
        except Exception:
            logger.exception("Unexpected query rewrite failure")
            return user_query

    # ─── Main Query Method ───────────────────────────────────────────────
    def query(
        self,
        user_query: str,
        service_type: Optional[str] = None,
        conversation_history: Optional[Sequence[ConversationMessage]] = None,
    ) -> Dict[str, Any]:
        """Query the configured vector or procedure-aware local retrieval pipeline.

        Flow:
          1. Use the configured Chroma retriever when requested.
          2. Otherwise resolve the procedure and preferred section.
          3. Retrieve with Chroma/BGE-M3 or the BM25 fallback.
          4. Synthesize with Gemini when available.
        """
        if getattr(self, "backend", "bm25") == "chroma":
            return self._query_vector(user_query, service_type, conversation_history)
        if not self.initialized:
            return self._fallback_query(
                user_query, service_type, reason="RAG engine offline"
            )

        # Compatibility for older in-process callers that injected a
        # LlamaIndex object directly. The production path never sets `index`.
        legacy_index = getattr(self, "index", None)
        if legacy_index is not None and not hasattr(self, "_bm25_index"):
            try:
                query_engine = legacy_index.as_query_engine(
                    similarity_top_k=5,
                    text_qa_template=getattr(self, "qa_prompt", None),
                )
                response = query_engine.query(user_query)
                return {
                    "answer": str(response), "sources": [], "confidence": 0.7,
                    "language": _detect_language(user_query),
                    "llm_status": "success",
                }
            except Exception as error:
                if _is_rate_limit_error(error):
                    return self._fallback_query(
                        user_query,
                        service_type,
                        reason="Gemini rate limited (HTTP 429)",
                    )
                return self._fallback_query(user_query, service_type, reason=str(error))

        detected_lang = _detect_language(user_query)
        resolved_service = service_type or _detect_service_from_query(user_query)
        section = detect_section(user_query)
        retrieval_query = build_retrieval_query(user_query, resolved_service, section)

        # Curated exact FAQs remain authoritative and avoid a generative model
        # paraphrasing a verified answer into a different procedure variant.
        if resolved_service:
            normalized_question = user_query.casefold().strip().rstrip("?؟.! ")
            procedure = load_normalized_procedure(resolved_service)
            for faq in procedure.get("faq") or []:
                stored_question = str(faq.get("question", ""))
                if stored_question.casefold().strip().rstrip("?؟.! ") == normalized_question:
                    path = procedure_path(resolved_service)
                    source = (
                        str(path.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
                        if path else resolved_service
                    )
                    chunk = {"procedure_id": resolved_service, "section": "faq", "score": 1.0}
                    logger.info(
                        "[RAG] backend=structured_exact_faq procedure_filter=%s "
                        "section_preference=%s top_chunks=%s",
                        resolved_service,
                        section,
                        [chunk],
                    )
                    return {
                        "answer": str(faq.get("answer", "")),
                        "sources": [source],
                        "confidence": 0.95,
                        "language": detected_lang,
                        "backend": "structured_exact_faq",
                        "procedure_id": resolved_service,
                        "section": "faq",
                        "retrieval_query": retrieval_query,
                        "retrieved_chunks": [chunk],
                        "llm_status": "fallback",
                        "llm_fallback_reason": "structured_exact_faq",
                    }

        try:
            llm_diagnostics: Dict[str, str] = {}
            vector_nodes = self._retrieve_chroma(
                retrieval_query=retrieval_query,
                procedure_id=resolved_service,
                section=section,
            )
            backend = "chroma_bge_m3" if vector_nodes else "bm25_fallback"
            rewritten_query = user_query
            bm25_nodes: List[ScoredNode] = []
            if not vector_nodes and self.bm25_retriever and self._bm25_index is not None:
                try:
                    # Query rewriting only benefits lexical BM25 retrieval.
                    # BGE-M3 embeds the multilingual retrieval query directly.
                    rewritten_query = self._rewrite_query(
                        user_query, llm_diagnostics
                    )
                    query_tokens = _tokenize_arabic(retrieval_query)
                    if rewritten_query != user_query:
                        query_tokens.extend(_tokenize_arabic(rewritten_query))
                    scores = self._bm25_index.get_scores(query_tokens)
                    indexed_scores = list(enumerate(scores))
                    service_scores = indexed_scores
                    if resolved_service:
                        service_scores = [
                            item for item in indexed_scores
                            if self._bm25_nodes[item[0]].metadata.get("procedure_id") == resolved_service
                        ]
                    max_score = max((float(item[1]) for item in service_scores), default=0.0)
                    # Strong enough to surface the intended section for terse
                    # follow-ups, while still keeping other procedure sections
                    # available as semantic fallbacks.
                    section_boost = max(0.75, abs(max_score) * 0.50)
                    service_scores.sort(
                        key=lambda item: float(item[1]) + (
                            section_boost
                            if section and self._bm25_nodes[item[0]].metadata.get("section") == section
                            else 0.0
                        ),
                        reverse=True,
                    )
                    top_indices = service_scores[:10]
                    for idx, score in top_indices:
                        preferred_section = (
                            section
                            and self._bm25_nodes[idx].metadata.get("section") == section
                        )
                        if score > 0 or preferred_section:
                            bm25_nodes.append(ScoredNode(self._bm25_nodes[idx], float(score)))
                    bm25_nodes = bm25_nodes[:5]
                except Exception as bm25_err:
                    print(f"[WARN] BM25 retrieval failed: {bm25_err}")

            combined = vector_nodes or bm25_nodes
            original_tokens = set(_tokenize_arabic(user_query))
            retrieved_tokens = {
                token
                for scored_node in combined
                for token in _tokenize_arabic(scored_node.node.text)
            }
            lexical_coverage = (
                len(original_tokens & retrieved_tokens) / len(original_tokens)
                if original_tokens else 0.0
            )
            if not vector_nodes and lexical_coverage < 0.25:
                fallback_reason = llm_diagnostics.get("fallback_reason") or (
                    "Retrieved context has insufficient lexical coverage"
                )
                return self._fallback_query(
                    user_query,
                    resolved_service,
                    reason=fallback_reason,
                )

            context_parts = [
                node.node.text
                for node in combined
                if node.node.text.strip()
            ]
            context = "\n\n---\n\n".join(context_parts)

            if not context.strip():
                fallback_reason = llm_diagnostics.get("fallback_reason") or (
                    "No relevant context found after procedure-aware search"
                )
                return self._fallback_query(
                    user_query,
                    resolved_service,
                    reason=fallback_reason,
                )

            prompt_tmpl = _prompt_with_history(conversation_history)
            prompt = prompt_tmpl.replace(
                "{context_str}", context
            ).replace("{query_str}", user_query)
            provider_unavailable = llm_diagnostics.get("fallback_reason") in {
                "gemini_rate_limited_http_429",
                "gemini_service_unavailable_http_503",
                "gemini_provider_server_error",
            }
            answer_text = (
                ""
                if provider_unavailable
                else _llm_generate(self._gemini, prompt, llm_diagnostics)
            )

            if not answer_text:
                answer_text = context_parts[0] if context_parts else ""
                if combined and combined[0].node.metadata.get("section") == "faq":
                    _, separator, faq_answer = answer_text.partition("جواب:")
                    if separator and faq_answer.strip():
                        answer_text = faq_answer.strip()

            sources: List[str] = []
            retrieved_chunks: List[Dict[str, Any]] = []
            for scored_node in combined:
                meta = scored_node.node.metadata
                fp = meta.get("file_path", "") or meta.get("file_name", "")
                if fp:
                    path = Path(fp)
                    try:
                        rel_path = str(path.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
                    except ValueError:
                        rel_path = str(fp).replace("\\", "/")
                    if rel_path not in sources:
                        sources.append(rel_path)
                retrieved_chunks.append({
                    "procedure_id": meta.get("procedure_id"),
                    "section": meta.get("section") or meta.get("node_type"),
                    "score": round(float(scored_node.score), 4),
                })

            logger.info(
                "[RAG] backend=%s procedure_filter=%s section_preference=%s top_chunks=%s",
                backend,
                resolved_service,
                section,
                retrieved_chunks,
            )

            n_results = len(combined)
            if n_results > 0:
                if vector_nodes:
                    top_similarity = max(0.0, min(1.0, float(vector_nodes[0].score)))
                    base = 0.50 + (0.35 * top_similarity)
                else:
                    base = 0.55 + (0.25 * lexical_coverage)
                source_boost = min(0.10, 0.02 * len(sources))
                confidence = round(min(0.98, base + source_boost), 2)
            else:
                confidence = 0.50

            uncertainty_markers = [
                "ما متأكدش",
                "لست متأكداً",
                "Je ne suis pas sûr",
            ]
            if any(marker in answer_text for marker in uncertainty_markers):
                confidence = 0.30
            if (
                vector_nodes
                and _detect_service_from_query(user_query) is None
                and lexical_coverage < 0.25
            ):
                # The procedure came from conversation state, but the current
                # turn has neither a recognizable administrative intent nor
                # lexical support in the retrieved evidence.
                confidence = min(confidence, 0.50)

            return {
                "answer": answer_text,
                "sources": (
                    sources
                    if sources
                    else [resolved_service or "knowledge_base"]
                ),
                "confidence": confidence,
                "language": detected_lang,
                "backend": backend,
                "procedure_id": resolved_service,
                "section": section,
                "retrieval_query": retrieval_query,
                "retrieved_chunks": retrieved_chunks,
                "llm_status": llm_diagnostics.get("status", "fallback"),
                "llm_fallback_reason": llm_diagnostics.get("fallback_reason"),
            }

        except Exception as e:
            if _is_rate_limit_error(e):
                return self._fallback_query(
                    user_query, resolved_service,
                    reason="Gemini rate limited (HTTP 429)",
                )
            logger.exception("Unexpected RAG query failure")
            return self._fallback_query(
                user_query, resolved_service, reason=str(e)
            )

    def _query_vector(self, user_query, service_type, conversation_history):
        from app.services.knowledge_base import load_service_knowledge
        language = _detect_language(user_query)
        service = service_type or _detect_service_from_query(user_query)
        # Give short follow-ups their procedure context without changing the
        # actual user question sent to the answer model.
        title = load_service_knowledge(service).get("service_name_ar", "") if service else ""
        query = f"{title}\n{user_query}" if title else user_query
        unavailable = ("Je n'ai pas trouvé de source suffisamment pertinente. Précisez la démarche ou votre situation."
                       if language == "french" else "ما لقيتش معلومات كافية وموثوقة. وضح ليا الخدمة أو الحالة ديالك.")
        try:
            if self._vector is None:
                raise RuntimeError(self._vector_error or "Vector retrieval unavailable")
            result = self._vector.retrieve(query, _normalize_service_filter(service) if service else None)
            payload = result.model_dump()
            payload.update(answer=unavailable, sources=[], language=language)
            if not result.chunks:
                payload["fallback_reason"] = "insufficient_vector_evidence"
                return payload
            context = "\n\n---\n\n".join(c.content for c in result.chunks)
            prompt = _prompt_with_history(conversation_history).replace("{context_str}", context).replace("{query_str}", user_query)
            payload["answer"] = _llm_generate(self._gemini, prompt)
            if not payload["answer"]:
                payload["answer"] = context
                payload["fallback_reason"] = "generation_unavailable_source_extracts"
            payload["sources"] = list(dict.fromkeys(str(c.metadata.get("file_path") or c.metadata.get("source_url") or "knowledge_base") for c in result.chunks))
            return payload
        except Exception as exc:
            print(f"[WARN] Vector query failed: {exc}")
            return {"answer": unavailable, "sources": [], "chunks": [], "confidence": 0.0,
                    "language": language, "backend": "chroma_bge_m3", "fallback_reason": "vector_backend_unavailable"}

    # ─── Fallback to Structured KB ───────────────────────────────────────
    def _fallback_query(
        self,
        user_query: str,
        service_type: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        """Fallback to local structured Knowledge Base if RAG is unavailable."""
        safe_reason = (
            "gemini_rate_limited_http_429"
            if "429" in reason or "rate limit" in reason.lower()
            else "gemini_service_unavailable_http_503"
            if "503" in reason or "service_unavailable" in reason.lower()
            else "rag_fallback"
        )
        llm_diagnostics: Dict[str, str] = {
            "status": "fallback",
            "fallback_reason": safe_reason,
        }
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
                    "backend": "bm25_fallback",
                    "procedure_id": None,
                    "section": detect_section(user_query),
                    "retrieved_chunks": [],
                    "llm_status": "fallback",
                    "llm_fallback_reason": safe_reason,
                }

            kb_ans = answer_with_metadata(
                resolved_service, user_query, use_rag=False
            )
            answer_text = kb_ans.answer

            # Polish with Gemini if available
            try:
                if (
                    self._gemini
                    and kb_ans.answer
                    and safe_reason not in {
                        "gemini_rate_limited_http_429",
                        "gemini_service_unavailable_http_503",
                    }
                ):
                    lang = _detect_language(user_query)
                    lang_inst = "en français" if lang == "french" else "بالدارجة المغربية"
                    prompt = (
                        f"Tu es OmniAgent, l'assistant officiel pour les démarches administratives marocaines.\n"
                        f"Informations officielles :\n{kb_ans.answer}\n\n"
                        f"Question : {user_query}\n"
                        f"Réponds de manière claire, structurée et chaleureuse {lang_inst} :"
                    )
                    polished = _llm_generate(self._gemini, prompt, llm_diagnostics)
                    if polished:
                        answer_text = polished
            except Exception:
                pass

            return {
                "answer": answer_text,
                "sources": kb_ans.sources,
                "confidence": kb_ans.confidence,
                "language": "darija",
                "fallback_reason": reason,
                "backend": "bm25_fallback",
                "procedure_id": resolved_service,
                "section": detect_section(user_query),
                "retrieved_chunks": [],
                "llm_status": llm_diagnostics.get("status", "fallback"),
                "llm_fallback_reason": llm_diagnostics.get("fallback_reason"),
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
                "backend": "bm25_fallback",
                "procedure_id": service_type,
                "section": detect_section(user_query),
                "retrieved_chunks": [],
                "llm_status": "fallback",
                "llm_fallback_reason": "rag_fallback_error",
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
    conversation_state: Optional[Dict[str, Any]] = None,
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
    if conversation_state is not None:
        from app.services.conversation_state import ConversationState
        state = ConversationState.model_validate(conversation_state)
        conversation_history = [*(conversation_history or []), {
            "role": "user",
            "content": "Conversation state (user context, not proof of document validity): "
                + state.model_dump_json()
                + "\nDo not ask again for supplied information. Ask only for necessary missing details.",
        }]
        service_type = service_type or state.current_procedure_id
    return engine.query(
        user_query=user_query,
        service_type=service_type,
        conversation_history=conversation_history,
    )
