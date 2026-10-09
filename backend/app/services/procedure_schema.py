"""Normalized procedure schema, routing, chunking, and suggestions."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KB_ROOT = PROJECT_ROOT / "tests" / "knowledge_base"
ALIASES_PATH = KB_ROOT / "procedure_aliases.json"

PROCEDURE_DIRS: dict[str, str] = {
    "identity_card": "identity_card",
    "residence_certificate": "residence",
    "birth_certificate": "birth",
    "marriage_contract": "marriage",
    "death_certificate": "death",
    "life_certificate": "life",
    "single_status_certificate": "single_status",
    "non_property_certificate": "non_property",
    "administrative_certificate": "administrative",
    "good_conduct_certificate": "good_conduct",
    "criminal_record": "criminal_record",
}
PROCEDURE_IDS_BY_DIR = {folder: procedure_id for procedure_id, folder in PROCEDURE_DIRS.items()}

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "required_documents": (
        "الوثائق", "وثائق", "الوراق", "وراق", "الأوراق", "اوراق",
        "مدارك", "documents", "pièces", "pieces", "dossier",
    ),
    "steps": (
        "الخطوات", "خطوات", "المراحل", "كيفاش", "كيفية", "الإجراءات",
        "procedure", "procédure", "etapes", "étapes",
    ),
    "processing_time": (
        "شحال كتشد", "شحال كتاخد", "شحال ديال الوقت", "المدة", "مدة",
        "الوقت", "وقت", "délai", "delai", "combien de temps", "durée", "duree",
    ),
    "fees": (
        "الرسوم", "رسوم", "الثمن", "ثمن", "واجبات", "كنخلص", "نخلص",
        "كتكلف", "prix", "coût", "cout", "frais", "fee", "cost",
    ),
    "personal_presence": (
        "الحضور", "نحضر", "يحضر", "شخصيا", "شخصياً", "خاصني نمشي",
        "présence", "presence", "personnellement", "en personne", "proxy",
    ),
    "where_to_apply": (
        "فين", "المكان", "أين", "اين", "نودع", "ندفع", "نصاوبها",
        "où", "ou déposer", "ou deposer", "adresse", "where",
    ),
    "validity": ("الصلاحية", "صالحة", "كتسالي", "validité", "validite", "valable"),
    "eligibility": ("الشروط", "شروط", "من يحق", "الأهلية", "condition", "éligible", "eligible"),
    "rejection_reasons": ("الرفض", "ترفض", "مرفوض", "rejet", "refus", "refusé", "refuse"),
}


@dataclass(frozen=True)
class ProcedureChunk:
    chunk_id: str
    text: str
    metadata: dict[str, str | int | float | bool]


@dataclass(frozen=True)
class ProcedureRoute:
    procedure_id: str | None
    section: str | None
    resolution: str
    explicit_procedure_id: str | None = None


@dataclass
class ConversationState:
    current_procedure_id: str | None = None
    turn_count: int = 0
    last_section: str | None = None

    def resolve(self, message: str) -> ProcedureRoute:
        explicit = detect_explicit_procedure(message)
        section = detect_section(message)
        if explicit:
            self.current_procedure_id = explicit
            resolution = "explicit"
        elif self.current_procedure_id:
            resolution = "inherited"
        else:
            resolution = "unresolved"
        self.turn_count += 1
        self.last_section = section
        return ProcedureRoute(self.current_procedure_id, section, resolution, explicit)


def _as_list(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    return value if isinstance(value, list) else [value]


def _as_text_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _as_list(value) if str(item).strip()]


def _grouped_list(value: Any) -> list[Any]:
    """Preserve legacy category names while files migrate incrementally."""
    if isinstance(value, dict):
        groups: list[dict[str, Any]] = []
        for category, items in value.items():
            normalized_items = _as_text_list(items)
            if normalized_items:
                groups.append({"category": str(category), "items": normalized_items})
        return groups
    if isinstance(value, list):
        normalized: list[Any] = []
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("items"), list):
                items = _as_text_list(item["items"])
                if items:
                    normalized.append({
                        "category": str(item.get("category") or "").strip(),
                        "items": items,
                    })
            elif str(item).strip():
                normalized.append(str(item).strip())
        return normalized
    return _as_text_list(value)


@lru_cache(maxsize=1)
def load_procedure_aliases() -> dict[str, list[str]]:
    try:
        raw = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(procedure_id): _as_text_list(aliases)
        for procedure_id, aliases in raw.items()
        if isinstance(aliases, list)
    }


def _searchable(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = text.replace("’", "'").replace("`", "'")
    return re.sub(r"\s+", " ", text).strip()


def detect_explicit_procedure(message: str) -> str | None:
    """Detect an explicitly named procedure using data-driven aliases."""
    haystack = _searchable(message)
    candidates: list[tuple[int, str]] = []
    for procedure_id, aliases in load_procedure_aliases().items():
        for alias in aliases:
            needle = _searchable(alias)
            if needle and re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", haystack):
                candidates.append((len(needle), procedure_id))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def detect_section(message: str) -> str | None:
    haystack = _searchable(message)
    matches: list[tuple[int, str]] = []
    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            needle = _searchable(alias)
            if needle and needle in haystack:
                matches.append((len(needle), section))
    return max(matches, key=lambda item: item[0])[1] if matches else None


def normalize_procedure(raw: dict[str, Any], procedure_id: str) -> dict[str, Any]:
    """Return the normalized schema for a migrated or legacy procedure file."""
    aliases = list(raw.get("aliases") or load_procedure_aliases().get(procedure_id, []))
    fees = raw.get("fees")
    if not isinstance(fees, dict):
        fees = {"amount": None, "notes": fees or None}
    else:
        fees = {"amount": fees.get("amount"), "notes": fees.get("notes")}

    where_to_apply = raw.get("where_to_apply")
    if not isinstance(where_to_apply, dict):
        authorities = _as_text_list(raw.get("issuing_authorities"))
        procedure_types = _as_text_list(raw.get("procedure_types"))
        where_to_apply = {"type": None, "description": "\n".join(authorities or procedure_types) or None}

    personal_presence = raw.get("personal_presence")
    if not isinstance(personal_presence, dict):
        searchable_source = " ".join(
            [str(raw.get("description", ""))]
            + _as_text_list(raw.get("conditions"))
            + _as_text_list(raw.get("procedure_types"))
        )
        explicitly_personal = any(
            marker in _searchable(searchable_source)
            for marker in ("شخصيا", "شخصياً", "personnellement", "en personne")
        )
        personal_presence = {"required": True if explicitly_personal else None, "exceptions": []}

    mapped = {
        "procedure_id", "title_ar", "title_fr", "aliases", "description", "eligibility",
        "required_documents", "steps", "where_to_apply", "personal_presence", "fees",
        "processing_time", "validity", "special_cases", "rejection_reasons", "faq",
        "sources", "last_updated", "service_name_ar", "service_name_fr", "service_name_en",
        "conditions", "general_steps", "validity_period", "issuing_authorities", "types", "note",
    }
    extra_sections = {
        key: value for key, value in raw.items()
        if key not in mapped and value not in (None, "", [], {})
    }
    # Keep legacy sections addressable during the migration window.  The
    # normalized equivalents above are authoritative, while these preserve
    # compatibility for callers/tests that still inspect old section names.
    for legacy_key in ("conditions", "issuing_authorities", "procedure_types"):
        if raw.get(legacy_key) not in (None, "", [], {}):
            extra_sections.setdefault(legacy_key, raw[legacy_key])
    special_cases = _as_text_list(raw.get("special_cases"))
    special_cases.extend(_as_text_list(raw.get("types")))
    special_cases.extend(_as_text_list(raw.get("note")))

    return {
        "procedure_id": raw.get("procedure_id") or procedure_id,
        "title_ar": raw.get("title_ar") or raw.get("service_name_ar") or procedure_id,
        "title_fr": raw.get("title_fr") or raw.get("service_name_fr") or None,
        "aliases": list(dict.fromkeys(aliases)),
        "description": raw.get("description") or "",
        "eligibility": _as_text_list(raw.get("eligibility") or raw.get("conditions")),
        "required_documents": _grouped_list(raw.get("required_documents")),
        "steps": _grouped_list(raw.get("steps") or raw.get("general_steps")),
        "where_to_apply": {"type": where_to_apply.get("type"), "description": where_to_apply.get("description")},
        "personal_presence": {
            "required": personal_presence.get("required"),
            "exceptions": _as_text_list(personal_presence.get("exceptions")),
        },
        "fees": fees,
        "processing_time": raw.get("processing_time"),
        "validity": raw.get("validity") or raw.get("validity_period"),
        "special_cases": list(dict.fromkeys(special_cases)),
        "rejection_reasons": _as_text_list(raw.get("rejection_reasons")),
        "faq": [
            {"question": str(item.get("question", "")).strip(), "answer": str(item.get("answer", "")).strip()}
            for item in _as_list(raw.get("faq"))
            if isinstance(item, dict) and item.get("question") and item.get("answer")
        ],
        "sources": _as_text_list(raw.get("sources")),
        "last_updated": raw.get("last_updated"),
        "extra_sections": extra_sections,
    }


def procedure_path(procedure_id: str) -> Path | None:
    folder = PROCEDURE_DIRS.get(procedure_id)
    if not folder:
        return None
    for path in sorted((KB_ROOT / folder).glob("*.json")):
        if path.name not in {"test_cases.json", "all_test_cases.json"}:
            return path
    return None


@lru_cache(maxsize=32)
def load_normalized_procedure(procedure_id: str) -> dict[str, Any]:
    path = procedure_path(procedure_id)
    if not path:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return normalize_procedure(raw, procedure_id)


def iter_normalized_procedures() -> Iterable[tuple[dict[str, Any], Path]]:
    for procedure_id in PROCEDURE_DIRS:
        path = procedure_path(procedure_id)
        procedure = load_normalized_procedure(procedure_id)
        if path and procedure:
            yield procedure, path


def _format_items(items: list[Any]) -> list[tuple[str | None, list[str]]]:
    grouped: list[tuple[str | None, list[str]]] = []
    plain: list[str] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("items"), list):
            grouped.append((str(item.get("category") or "").strip() or None, _as_text_list(item["items"])))
        elif str(item).strip():
            plain.append(str(item).strip())
    if plain:
        grouped.insert(0, (None, plain))
    return grouped


def _language_of(text: str) -> str:
    arabic = len(re.findall(r"[\u0600-\u06ff]", text))
    latin = len(re.findall(r"[a-zA-ZÀ-ÿ]", text))
    if arabic and latin and min(arabic, latin) / max(arabic, latin) > 0.25:
        return "multilingual"
    return "ar" if arabic >= latin else "fr"


def generate_procedure_chunks(
    procedure: dict[str, Any], source_path: Path, source_type: str = "official"
) -> list[ProcedureChunk]:
    """Create one retrievable chunk per meaningful procedure section."""
    procedure_id = str(procedure["procedure_id"])
    title = str(procedure.get("title_ar") or procedure_id)
    relative_path = str(source_path.relative_to(KB_ROOT)).replace("\\", "/")
    folder = PROCEDURE_DIRS.get(procedure_id, source_path.parent.name)
    chunks: list[ProcedureChunk] = []

    def add(section: str, text: str, subsection: str | None = None) -> None:
        clean = text.strip()
        if not clean:
            return
        digest = hashlib.sha256(f"{procedure_id}|{section}|{subsection or ''}|{clean}".encode()).hexdigest()[:24]
        metadata: dict[str, str | int | float | bool] = {
            "procedure_id": procedure_id,
            "section": section,
            "language": _language_of(clean),
            "source_type": source_type,
            "file_path": relative_path,
            "service_type": folder,
            "node_type": section,
        }
        if subsection:
            metadata["subsection"] = subsection
        chunks.append(ProcedureChunk(f"{procedure_id}:{section}:{digest}", clean, metadata))

    overview = [title]
    if procedure.get("title_fr"):
        overview.append(str(procedure["title_fr"]))
    if procedure.get("aliases"):
        overview.append("الأسماء المتداولة / Alias: " + "، ".join(map(str, procedure["aliases"])))
    if procedure.get("description"):
        overview.append(str(procedure["description"]))
    add("description", "\n".join(overview))

    for section, heading in (
        ("eligibility", "شروط الاستفادة"),
        ("special_cases", "حالات خاصة"),
        ("rejection_reasons", "أسباب الرفض"),
    ):
        items = _as_text_list(procedure.get(section))
        if items:
            add(section, f"{heading} لـ{title}:\n" + "\n".join(f"- {item}" for item in items))

    for section, heading in (("required_documents", "الوثائق المطلوبة"), ("steps", "الخطوات")):
        for category, items in _format_items(procedure.get(section) or []):
            suffix = f" ({category})" if category else ""
            body = (
                "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))
                if section == "steps" else "\n".join(f"- {item}" for item in items)
            )
            add(section, f"{heading} لـ{title}{suffix}:\n{body}", category)

    where = procedure.get("where_to_apply") or {}
    where_text = "\n".join(str(value) for value in (where.get("type"), where.get("description")) if value)
    if where_text:
        add("where_to_apply", f"مكان طلب {title}:\n{where_text}")

    presence = procedure.get("personal_presence") or {}
    if presence.get("required") is not None or presence.get("exceptions"):
        required_text = (
            "الحضور الشخصي مطلوب." if presence.get("required") is True
            else "الحضور الشخصي غير مطلوب." if presence.get("required") is False else ""
        )
        exceptions = "\n".join(f"- {item}" for item in _as_text_list(presence.get("exceptions")))
        add("personal_presence", f"{title}: {required_text}\n{exceptions}")

    fees = procedure.get("fees") or {}
    fee_parts = [str(value) for value in (fees.get("amount"), fees.get("notes")) if value not in (None, "")]
    if fee_parts:
        add("fees", f"رسوم {title}: " + " — ".join(fee_parts))
    if procedure.get("processing_time"):
        add("processing_time", f"مدة معالجة {title}: {procedure['processing_time']}")
    if procedure.get("validity"):
        add("validity", f"مدة صلاحية {title}: {procedure['validity']}")

    for index, faq in enumerate(procedure.get("faq") or [], 1):
        add("faq", f"سؤال: {faq['question']}\nجواب: {faq['answer']}", str(index))

    for key, value in (procedure.get("extra_sections") or {}).items():
        if isinstance(value, list):
            rendered = "\n".join(f"- {item}" for item in value)
        elif isinstance(value, dict):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        add(str(key), f"{title} - {key}:\n{rendered}")
    return chunks


def build_retrieval_query(message: str, procedure_id: str | None, section: str | None) -> str:
    """Build an embedding query from the current turn and resolved state only."""
    parts = [message.strip()]
    if procedure_id:
        procedure = load_normalized_procedure(procedure_id)
        title = procedure.get("title_ar") or procedure.get("title_fr") or procedure_id
        parts.append(f"الإجراء المقصود: {title}")
    if section:
        parts.append(f"القسم المطلوب: {section}")
    return "\n".join(part for part in parts if part)


SUGGESTION_TEMPLATES: dict[str, dict[str, str]] = {
    "required_documents": {"ar": "ما هي الوثائق المطلوبة؟", "darija": "شنو الوثائق المطلوبة؟", "fr": "Quels documents sont requis ?"},
    "personal_presence": {"ar": "هل الحضور الشخصي ضروري؟", "darija": "واش الحضور الشخصي ضروري؟", "fr": "La présence personnelle est-elle obligatoire ?"},
    "where_to_apply": {"ar": "أين يمكنني تقديم الطلب؟", "darija": "فين نقدر نقدّم الطلب؟", "fr": "Où puis-je déposer la demande ?"},
    "processing_time": {"ar": "كم تستغرق المعالجة؟", "darija": "شحال كتحتاج من الوقت؟", "fr": "Quel est le délai de traitement ?"},
    "fees": {"ar": "هل توجد رسوم؟", "darija": "واش كاينة شي رسوم؟", "fr": "Y a-t-il des frais ?"},
    "steps": {"ar": "ما هي خطوات الطلب؟", "darija": "شنو هي الخطوات؟", "fr": "Quelles sont les étapes ?"},
    "validity": {"ar": "ما مدة صلاحيتها؟", "darija": "شحال كتبقى صالحة؟", "fr": "Quelle est sa durée de validité ?"},
    "eligibility": {"ar": "ما شروط الاستفادة؟", "darija": "شنو الشروط؟", "fr": "Quelles sont les conditions ?"},
    "rejection_reasons": {"ar": "ما أسباب رفض الطلب؟", "darija": "علاش يقدر يترفض الطلب؟", "fr": "Quels sont les motifs de refus ?"},
}


def suggested_questions(procedure_id: str | None, language: str = "darija", limit: int = 6) -> list[str]:
    if not procedure_id:
        return []
    procedure = load_normalized_procedure(procedure_id)
    if not procedure:
        return []
    available: list[str] = []
    for section, translations in SUGGESTION_TEMPLATES.items():
        value = procedure.get(section)
        if section == "fees":
            value = (value or {}).get("amount") or (value or {}).get("notes")
        elif section == "personal_presence":
            value = (value or {}).get("required") is not None or bool((value or {}).get("exceptions"))
        elif section == "where_to_apply":
            value = (value or {}).get("type") or (value or {}).get("description")
        if value not in (None, "", [], {}, False):
            available.append(translations.get(language, translations["darija"]))
    available.extend(
        str(item["question"]).strip()
        for item in procedure.get("faq") or []
        if item.get("question")
    )
    return list(dict.fromkeys(available))[:limit]
