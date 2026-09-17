"""Audio processing service for Darija / Arabic / French voice workflows.

Handles:
  - Speech-to-Text (STT) via Gemini Flash Audio
  - Voice-ready text sanitization (strip markdown, tables, links, emojis)
  - Text-to-Speech (TTS) via gTTS
  - Browser Web Speech API configuration hints
"""

from __future__ import annotations

import base64
import io
import logging
import re
from typing import Any

import google.generativeai as genai  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Supported audio MIME types ──────────────────────────────────────────────
ALLOWED_AUDIO_MIMES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mp3",
    "audio/mpeg",
    "audio/ogg",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
    "audio/aac",
    "audio/flac",
}

# ── Darija-specialised transcription prompt ─────────────────────────────────
_TRANSCRIBE_SYSTEM_PROMPT = """\
You are an expert speech-to-text transcriber specialised in Moroccan Darija \
(الدارجة المغربية), Modern Standard Arabic (العربية الفصحى), and French.

Rules:
1. Transcribe the audio VERBATIM — do NOT summarise, translate, or interpret.
2. Preserve the original language and script used by the speaker.
3. If the speaker code-switches between Darija, Arabic, and French, keep each \
   segment in its original language and script.
4. Use Arabic script (عربي) for Darija and Arabic segments unless the speaker \
   clearly uses Latin/Arabizi.
5. Moroccan administrative vocabulary to recognise correctly:
   - شهادة السكنى (résidence certificate), شهادة الميلاد (birth certificate)
   - عقد الزواج (marriage contract), شهادة الوفاة (death certificate)
   - شهادة الحياة (life certificate), شهادة العزوبة (single status)
   - شهادة عدم الملكية (non-property certificate)
   - السجل العدلي (criminal record), شهادة حسن السيرة (good conduct)
   - المقدم (Moqadem), المقاطعة (Mouqata'a), البلدية (Baladiya)
   - الحالة المدنية (civil status), الجماعة (commune)
   - CIN, CNSS, RAMED, CMR, Massar
6. If the audio is silent or unintelligible, respond with exactly: [SILENCE]
7. Output ONLY the transcription — no explanations, no labels.
"""


# ═══════════════════════════════════════════════════════════════════════════ #
#  Speech-to-Text
# ═══════════════════════════════════════════════════════════════════════════ #

def transcribe_audio(
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    language_hint: str = "darija",
) -> dict[str, Any]:
    """Transcribe audio bytes using Gemini Flash Audio.

    Args:
        audio_bytes: Raw audio file bytes.
        mime_type:   MIME type of the audio (e.g. ``audio/webm``).
        language_hint: Preferred output language context
                       (``darija``, ``ar``, ``fr``).

    Returns:
        Dict with keys ``text``, ``language``, ``confidence``, ``error``.
    """
    if mime_type not in ALLOWED_AUDIO_MIMES:
        return {
            "text": "",
            "language": language_hint,
            "confidence": 0.0,
            "error": f"Unsupported audio format: {mime_type}. "
                     f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_MIMES))}",
        }

    max_bytes = settings.max_audio_upload_bytes
    if len(audio_bytes) > max_bytes:
        return {
            "text": "",
            "language": language_hint,
            "confidence": 0.0,
            "error": f"Audio too large ({len(audio_bytes):,} bytes). "
                     f"Max allowed: {max_bytes:,} bytes.",
        }

    if len(audio_bytes) == 0:
        return {
            "text": "",
            "language": language_hint,
            "confidence": 0.0,
            "error": "Empty audio file.",
        }

    api_key = settings.google_api_key
    if not api_key:
        return {
            "text": "",
            "language": language_hint,
            "confidence": 0.0,
            "error": "GOOGLE_API_KEY is not configured on the server.",
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            settings.gemini_audio_model,
            system_instruction=_TRANSCRIBE_SYSTEM_PROMPT,
        )

        # Build language hint addendum
        lang_map = {
            "darija": "The speaker is likely using Moroccan Darija (الدارجة). "
                      "Transcribe in Arabic script.",
            "ar":     "The speaker is likely using Arabic. "
                      "Transcribe in Arabic script.",
            "fr":     "The speaker is likely using French. "
                      "Transcribe in Latin script.",
        }
        hint = lang_map.get(language_hint, lang_map["darija"])

        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": audio_bytes},
                f"Transcribe this audio. {hint}",
            ],
            generation_config=genai.GenerationConfig(temperature=0.0),
        )

        transcription = (response.text or "").strip()

        if not transcription or transcription == "[SILENCE]":
            return {
                "text": "",
                "language": language_hint,
                "confidence": 0.0,
                "error": "No speech detected in the audio.",
            }

        # Detect predominant language of the transcription
        detected = _detect_language(transcription)

        return {
            "text": transcription,
            "language": detected,
            "confidence": 0.92,  # Gemini Flash heuristic baseline
            "error": None,
        }
    except Exception as exc:
        logger.exception("Audio transcription failed")
        return {
            "text": "",
            "language": language_hint,
            "confidence": 0.0,
            "error": f"Transcription failed: {exc}",
        }


def _detect_language(text: str) -> str:
    """Heuristic language detection from transcribed text."""
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    latin_chars = len(re.findall(r"[a-zA-ZÀ-ÿ]", text))
    total = arabic_chars + latin_chars or 1
    if arabic_chars / total > 0.5:
        # Could be Darija or MSA — default to darija for this app
        return "darija"
    if latin_chars / total > 0.5:
        return "fr"
    return "darija"


# ═══════════════════════════════════════════════════════════════════════════ #
#  Voice-Ready Text Sanitization
# ═══════════════════════════════════════════════════════════════════════════ #

def sanitize_for_voice(text: str, language: str = "darija") -> str:
    """Transform a markdown-rich AI response into concise spoken text.

    Strips markdown formatting, converts tables to spoken lists,
    removes emojis, citations, and returns natural conversational text.
    """
    if not text:
        return ""

    result = text

    # ── 1. Remove code blocks ──
    result = re.sub(r"```[\s\S]*?```", "", result)
    result = re.sub(r"`([^`]+)`", r"\1", result)

    # ── 2. Convert markdown tables to spoken lists ──
    result = _convert_tables_to_spoken(result, language)

    # ── 3. Strip markdown headers ──
    result = re.sub(r"^#{1,6}\s*", "", result, flags=re.MULTILINE)

    # ── 4. Strip bold / italic / strikethrough ──
    result = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", result)
    result = re.sub(r"\*\*(.+?)\*\*", r"\1", result)
    result = re.sub(r"\*(.+?)\*", r"\1", result)
    result = re.sub(r"__(.+?)__", r"\1", result)
    result = re.sub(r"_(.+?)_", r"\1", result)
    result = re.sub(r"~~(.+?)~~", r"\1", result)

    # ── 5. Strip markdown links — keep link text ──
    result = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", result)

    # ── 6. Strip images ──
    result = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", result)

    # ── 7. Remove horizontal rules ──
    result = re.sub(r"^[-*_]{3,}\s*$", "", result, flags=re.MULTILINE)

    # ── 8. Remove blockquotes ──
    result = re.sub(r"^>\s?", "", result, flags=re.MULTILINE)

    # ── 9. Clean bullet points — flatten to natural sentences ──
    result = re.sub(r"^[\s]*[-•*+]\s+", "• ", result, flags=re.MULTILINE)

    # ── 10. Remove citation references like [1], [2] ──
    result = re.sub(r"\[\d+\]", "", result)

    # ── 11. Remove emojis and special symbols ──
    result = re.sub(
        r"[\U00010000-\U0010FFFF]"   # Supplementary planes (most emojis)
        r"|[\u2600-\u27BF]"           # Misc symbols
        r"|[\u2B50-\u2BFF]"           # Additional symbols
        r"|[\uFE00-\uFE0F]"           # Variation selectors
        r"|[\u200D]",                  # Zero-width joiner
        "",
        result,
    )

    # ── 12. Collapse multiple blank lines ──
    result = re.sub(r"\n{3,}", "\n\n", result)

    # ── 13. Clean up extra whitespace ──
    result = re.sub(r"[ \t]+", " ", result)
    result = "\n".join(line.strip() for line in result.splitlines())
    result = result.strip()

    return result


def _convert_tables_to_spoken(text: str, language: str) -> str:
    """Convert markdown tables to spoken list format.

    Example markdown table:
        | الوثيقة | المكان |
        |---------|--------|
        | CIN     | البلدية |
        | شهادة   | المقاطعة |

    Becomes (for darija/ar):
        أولاً: CIN، المكان: البلدية.
        ثانياً: شهادة، المكان: المقاطعة.
    """
    lines = text.split("\n")
    output_lines: list[str] = []
    i = 0

    # Arabic ordinals for voice reading
    ordinals_ar = [
        "أولاً", "ثانياً", "ثالثاً", "رابعاً", "خامساً",
        "سادساً", "سابعاً", "ثامناً", "تاسعاً", "عاشراً",
    ]
    ordinals_fr = [
        "Premièrement", "Deuxièmement", "Troisièmement",
        "Quatrièmement", "Cinquièmement", "Sixièmement",
        "Septièmement", "Huitièmement", "Neuvièmement", "Dixièmement",
    ]

    ordinals = ordinals_fr if language == "fr" else ordinals_ar

    while i < len(lines):
        line = lines[i].strip()

        # Detect table start: line with pipes
        if "|" in line and line.startswith("|") and line.endswith("|"):
            # Parse header row
            headers = [
                cell.strip()
                for cell in line.strip("|").split("|")
                if cell.strip()
            ]

            # Skip separator row (|---|---|)
            i += 1
            if i < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i].strip()):
                i += 1

            # Parse data rows
            row_idx = 0
            while i < len(lines):
                row_line = lines[i].strip()
                if not ("|" in row_line and row_line.startswith("|") and row_line.endswith("|")):
                    break
                cells = [
                    cell.strip()
                    for cell in row_line.strip("|").split("|")
                    if cell.strip()
                ]
                if cells:
                    ordinal = ordinals[row_idx] if row_idx < len(ordinals) else f"{row_idx + 1}"
                    parts = []
                    for h, c in zip(headers, cells):
                        parts.append(f"{h}: {c}")
                    spoken = f"{ordinal}: {', '.join(parts)}."
                    output_lines.append(spoken)
                    row_idx += 1
                i += 1
        else:
            output_lines.append(lines[i])
            i += 1

    return "\n".join(output_lines)


# ═══════════════════════════════════════════════════════════════════════════ #
#  Text-to-Speech Synthesis
# ═══════════════════════════════════════════════════════════════════════════ #

def synthesize_speech(text: str, language: str = "ar") -> bytes:
    """Generate MP3 audio bytes from text using gTTS.

    Args:
        text: The text to speak (should already be sanitized for voice).
        language: Language code — ``ar`` for Arabic/Darija, ``fr`` for French.

    Returns:
        MP3 audio bytes.

    Raises:
        ValueError: If text is empty.
        RuntimeError: If TTS synthesis fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    # Map app language codes to gTTS language codes
    gtts_lang = "fr" if language == "fr" else "ar"

    try:
        from gtts import gTTS  # type: ignore

        tts = gTTS(text=text.strip(), lang=gtts_lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_bytes = buf.read()
        logger.info(
            "TTS synthesis OK: %d chars → %d bytes MP3 (lang=%s)",
            len(text), len(audio_bytes), gtts_lang,
        )
        return audio_bytes
    except Exception as exc:
        logger.exception("TTS synthesis failed")
        raise RuntimeError(f"TTS synthesis failed: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════ #
#  Browser Web Speech API Configuration
# ═══════════════════════════════════════════════════════════════════════════ #

def get_browser_voice_config(language: str = "darija") -> dict[str, Any]:
    """Return recommended browser Web Speech API configuration.

    The frontend can use these parameters with ``SpeechSynthesisUtterance``
    and ``SpeechRecognition`` for optimal Darija / Arabic / French support.
    """
    configs = {
        "darija": {
            "tts": {
                "lang": "ar-MA",
                "fallbackLangs": ["ar-SA", "ar"],
                "rate": 0.95,
                "pitch": 1.0,
                "volume": 1.0,
            },
            "stt": {
                "lang": "ar-MA",
                "fallbackLangs": ["ar-SA", "ar"],
                "continuous": False,
                "interimResults": True,
                "maxAlternatives": 3,
            },
            "instructions": (
                "For Moroccan Darija, use ar-MA locale. "
                "If unavailable, fall back to ar-SA or ar. "
                "Set rate slightly below 1.0 for clearer pronunciation."
            ),
        },
        "ar": {
            "tts": {
                "lang": "ar-SA",
                "fallbackLangs": ["ar"],
                "rate": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
            },
            "stt": {
                "lang": "ar-SA",
                "fallbackLangs": ["ar"],
                "continuous": False,
                "interimResults": True,
                "maxAlternatives": 3,
            },
            "instructions": "Standard Arabic voice configuration.",
        },
        "fr": {
            "tts": {
                "lang": "fr-MA",
                "fallbackLangs": ["fr-FR", "fr"],
                "rate": 1.0,
                "pitch": 1.0,
                "volume": 1.0,
            },
            "stt": {
                "lang": "fr-MA",
                "fallbackLangs": ["fr-FR", "fr"],
                "continuous": False,
                "interimResults": True,
                "maxAlternatives": 3,
            },
            "instructions": (
                "For Moroccan French, prefer fr-MA locale. "
                "Falls back to fr-FR."
            ),
        },
    }
    return configs.get(language, configs["darija"])
