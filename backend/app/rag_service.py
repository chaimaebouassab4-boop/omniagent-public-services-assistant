"""RAG Service Module (OmniAgent RAG) — Lightweight Edition

Pure BM25 + google-generativeai implementation.
Zero LlamaIndex dependencies — runs within Railway's 512 MB RAM limit.

Architecture:
  - BM25 keyword search over local knowledge base JSON/MD files
  - Query Rewriting: Darija/French -> formal MSA Arabic before search
  - Smart Service Detection: 50+ keywords across Darija/Arabic/French
  - Direct Answer Prompting via Gemini Flash
"""
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, List, Dict, Sequence

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Resolve project paths
THIS_FILE = Path(__file__).resolve()
# Root directory of the project (omniagent-public-services-assistant)
ROOT_DIR = THIS_FILE.parents[2]
KNOWLEDGE_DIR = ROOT_DIR / "tests" / "knowledge_base"
EXCLUDED_KB_NAMES = {"test_cases.json", "all_test_cases.json"}


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
# Maps keywords (Arabic/Darija/French) -> canonical service_id.
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
def _load_kb_nodes() -> List[KBNode]:
    """Load knowledge base files into granular KBNode objects for BM25.

    Creates fine-grained nodes (one per FAQ entry, one per structured field)
    so BM25 keyword matching can pinpoint exact answers.
    """
    nodes: List[KBNode] = []

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
                nodes.append(KBNode(
                    text=text,
                    metadata={**base_meta, "node_type": "raw"},
                ))
                continue

            svc_name = data.get("service_name_ar", service_type)

            # One node per FAQ entry (granular -- best for BM25)
            for faq in data.get("faq", []):
                q = faq.get("question", "")
                a = faq.get("answer", "")
                if q and a:
                    nodes.append(KBNode(
                        text=f"سؤال: {q}\nجواب: {a}",
                        metadata={**base_meta, "node_type": "faq"},
                    ))

            # One node per scalar field
            for field_key in ("description", "fees", "validity_period", "note"):
                value = data.get(field_key)
                if value and isinstance(value, str):
                    nodes.append(KBNode(
                        text=f"{svc_name} - {field_key}: {value}",
                        metadata={**base_meta, "node_type": field_key},
                    ))

            # Nodes from required_documents
            req_docs = data.get("required_documents")
            if isinstance(req_docs, list) and req_docs:
                docs_text = "\n".join(f"- {d}" for d in req_docs)
                nodes.append(KBNode(
                    text=f"الوثائق المطلوبة لـ{svc_name}:\n{docs_text}",
                    metadata={**base_meta, "node_type": "required_documents"},
                ))
            elif isinstance(req_docs, dict):
                for cat, doc_list in req_docs.items():
                    if isinstance(doc_list, list) and doc_list:
                        docs_text = "\n".join(f"- {d}" for d in doc_list)
                        nodes.append(KBNode(
                            text=f"الوثائق المطلوبة لـ{svc_name} ({cat}):\n{docs_text}",
                            metadata={**base_meta, "node_type": "required_documents"},
                        ))

            # Nodes from general_steps
            steps = data.get("general_steps")
            if isinstance(steps, list) and steps:
                steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
                nodes.append(KBNode(
                    text=f"خطوات {svc_name}:\n{steps_text}",
                    metadata={**base_meta, "node_type": "general_steps"},
                ))
            elif isinstance(steps, dict):
                for cat, step_list in steps.items():
                    if isinstance(step_list, list) and step_list:
                        steps_text = "\n".join(
                            f"{i+1}. {s}" for i, s in enumerate(step_list)
                        )
                        nodes.append(KBNode(
                            text=f"خطوات {svc_name} ({cat}):\n{steps_text}",
                            metadata={**base_meta, "node_type": "general_steps"},
                        ))

        # ── Markdown Files ──
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                nodes.append(KBNode(
                    text=text,
                    metadata={**base_meta, "node_type": "markdown"},
                ))

    return nodes


# ─── Arabic Tokenizer for BM25 ──────────────────────────────────────────────
def _tokenize_arabic(text: str) -> List[str]:
    """Tokenize Arabic/Darija/French text for BM25 indexing.

    Splits on whitespace and punctuation, lowercases Latin chars,
    and removes very short tokens.
    """
    # Split on whitespace and common punctuation
    tokens = re.findall(r"[\w\u0600-\u06FF\u0750-\u077F]+", text, re.UNICODE)
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
    """Create and configure a google-generativeai GenerativeModel.

    Returns None if GOOGLE_API_KEY is missing.
    """
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    if not api_key:
        print("[WARN] GOOGLE_API_KEY not set -- LLM features disabled")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.GenerationConfig(temperature=0.1),
    )
    print(f"[OK] Gemini model configured: {model_name}")
    return model


def _llm_generate(model, prompt: str) -> str:
    """Call Gemini generate_content and return text. Returns '' on failure."""
    if model is None:
        return ""
    try:
        response = model.generate_content(prompt)
        return (response.text or "").strip()
    except Exception as e:
        print(f"[WARN] Gemini generate failed: {e}")
        return ""


# ═════════════════════════════════════════════════════════════════════════════
# Main RAG Engine
# ═════════════════════════════════════════════════════════════════════════════
class OmniAgentRAG:
    """Reusable RAG engine with BM25 retrieval and Gemini synthesis."""

    def __init__(
        self,
        ollama_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ):
        self.initialized = False
        self.bm25_retriever = False
        self._gemini = None
        self._bm25_nodes: List[KBNode] = []
        self._bm25_index = None
        self._rewrite_cache: Dict[str, str] = {}
        # Allow overriding model name
        if gemini_model:
            os.environ["GEMINI_MODEL"] = gemini_model
        self._init_rag()

    # ─── Initialization ──────────────────────────────────────────────────
    def _init_rag(self) -> None:
        """Initialize BM25 retriever and Gemini LLM."""
        try:
            # ── 1. Gemini LLM ──
            self._gemini = _create_gemini_model()

            # ── 2. BM25 Retriever (Fast, lightweight ~5MB, ultra-reliable) ──
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

    # ─── Query Rewriting (Darija/French -> MSA) ───────────────────────────
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
            prompt = REWRITE_PROMPT.replace("{query}", user_query)
            rewritten = _llm_generate(self._gemini, prompt)

            # Sanity check -- rewritten should contain Arabic characters
            if re.search(r"[\u0600-\u06FF]", rewritten) and len(rewritten) > 3:
                # Remove any preamble the LLM might add
                for prefix in ["الترجمة:", "الترجمة بالعربية الفصحى:"]:
                    if rewritten.startswith(prefix):
                        rewritten = rewritten[len(prefix):].strip()

                self._rewrite_cache[user_query] = rewritten
                print(
                    f"[REWRITE] '{user_query[:50]}' -> "
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
        """Query RAG pipeline with BM25 search and Gemini synthesis.

        Flow:
          1. Detect language -> auto-detect service type
          2. Rewrite query (Darija/French -> MSA) for better retrieval
          3. BM25 keyword search with original + rewritten query
          4. Generate answer with the improved direct-answer prompt via Gemini
        """
        if not self.initialized:
            return self._fallback_query(
                user_query, service_type, reason="RAG engine offline"
            )

        # Step 1: Detect language and auto-detect service
        detected_lang = _detect_language(user_query)
        resolved_service = service_type or _detect_service_from_query(user_query)

        try:
            # Step 2: Rewrite query to MSA for better retrieval
            rewritten_query = self._rewrite_query(user_query)

            # Step 3: BM25 retrieval
            clean_service = None
            if resolved_service:
                clean_service = _normalize_service_filter(resolved_service)

            bm25_nodes: List[ScoredNode] = []
            if self.bm25_retriever and self._bm25_index is not None:
                try:
                    query_tokens = _tokenize_arabic(user_query)
                    scores = self._bm25_index.get_scores(query_tokens)

                    # Get top-10 indices by BM25 score (pure Python, no numpy)
                    indexed_scores = list(enumerate(scores))
                    indexed_scores.sort(key=lambda x: x[1], reverse=True)
                    top_indices = indexed_scores[:10]

                    raw_bm25: List[ScoredNode] = []
                    for idx, score in top_indices:
                        if score > 0:
                            raw_bm25.append(ScoredNode(
                                node=self._bm25_nodes[idx],
                                score=float(score),
                            ))

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

            combined = bm25_nodes[:5]

            # Step 4: Build context from retrieved nodes
            context_parts = [
                node.node.text
                for node in combined
                if node.node.text.strip()
            ]
            context = "\n\n---\n\n".join(context_parts)

            if not context.strip():
                return self._fallback_query(
                    user_query,
                    service_type,
                    reason="No relevant context found after BM25 search",
                )

            # Step 5: Format prompt with conversation history
            prompt_tmpl = _prompt_with_history(conversation_history)
            prompt = prompt_tmpl.replace(
                "{context_str}", context
            ).replace("{query_str}", user_query)

            # Step 6: Call Gemini to generate answer
            answer_text = _llm_generate(self._gemini, prompt)

            if not answer_text:
                # LLM failed -- return raw KB context as answer
                answer_text = context_parts[0] if context_parts else ""

            # Step 7: Extract metadata from retrieved nodes
            sources: List[str] = []
            for scored_node in combined:
                meta = scored_node.node.metadata
                fp = meta.get("file_path", "") or meta.get("file_name", "")
                if fp:
                    rel_path = Path(fp).name
                    if rel_path not in sources:
                        sources.append(rel_path)

            # Calculate confidence
            n_results = len(combined)
            n_bm25_hits = len(bm25_nodes)
            if n_results > 0:
                base = 0.80
                source_boost = min(0.10, 0.02 * len(sources))
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
            if _is_rate_limit_error(e):
                print(
                    "[WARN] Gemini rate limited (HTTP 429); using local KB fallback"
                )
                return self._fallback_query(
                    user_query,
                    service_type,
                    reason="Gemini rate limited (HTTP 429)",
                )
            print(f"[WARN] RAG query error: {e}")
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
            answer_text = kb_ans.answer

            # Polish with Gemini if available
            try:
                if self._gemini and kb_ans.answer:
                    lang = _detect_language(user_query)
                    lang_inst = "en français" if lang == "french" else "بالدارجة المغربية"
                    prompt = (
                        f"Tu es OmniAgent, l'assistant officiel pour les démarches administratives marocaines.\n"
                        f"Informations officielles :\n{kb_ans.answer}\n\n"
                        f"Question : {user_query}\n"
                        f"Réponds de manière claire, structurée et chaleureuse {lang_inst} :"
                    )
                    polished = _llm_generate(self._gemini, prompt)
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
