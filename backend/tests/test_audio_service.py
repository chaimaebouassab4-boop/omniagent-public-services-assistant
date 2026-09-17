"""Unit tests for the audio processing service.

Run with:
    cd backend && python -m pytest tests/test_audio_service.py -v
"""

from __future__ import annotations

import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.audio_service import (
    _detect_language,
    get_browser_voice_config,
    sanitize_for_voice,
    ALLOWED_AUDIO_MIMES,
)


# ═══════════════════════════════════════════════════════════════════════════ #
#  sanitize_for_voice
# ═══════════════════════════════════════════════════════════════════════════ #

class TestSanitizeForVoice:
    """Tests for markdown → voice text transformation."""

    def test_strips_bold(self):
        assert sanitize_for_voice("هذا **نص** مهم") == "هذا نص مهم"

    def test_strips_italic(self):
        assert sanitize_for_voice("هذا *نص* مهم") == "هذا نص مهم"

    def test_strips_headers(self):
        result = sanitize_for_voice("## عنوان\nمحتوى")
        assert "##" not in result
        assert "عنوان" in result
        assert "محتوى" in result

    def test_strips_links(self):
        result = sanitize_for_voice("[اضغط هنا](https://example.com)")
        assert "اضغط هنا" in result
        assert "https://example.com" not in result
        assert "[" not in result

    def test_strips_images(self):
        result = sanitize_for_voice("![صورة](https://img.com/x.png)")
        assert "https://img.com" not in result

    def test_strips_code_blocks(self):
        result = sanitize_for_voice("قبل\n```python\nprint('hello')\n```\nبعد")
        assert "```" not in result
        assert "قبل" in result
        assert "بعد" in result

    def test_strips_inline_code(self):
        result = sanitize_for_voice("استخدم `CIN` للتسجيل")
        assert "`" not in result
        assert "CIN" in result

    def test_strips_horizontal_rules(self):
        result = sanitize_for_voice("قبل\n---\nبعد")
        assert "---" not in result

    def test_strips_blockquotes(self):
        result = sanitize_for_voice("> هذا اقتباس")
        assert ">" not in result
        assert "هذا اقتباس" in result

    def test_strips_strikethrough(self):
        result = sanitize_for_voice("~~محذوف~~")
        assert "~~" not in result
        assert "محذوف" in result

    def test_strips_citations(self):
        result = sanitize_for_voice("المصدر [1] والمصدر [2]")
        assert "[1]" not in result
        assert "[2]" not in result

    def test_empty_input(self):
        assert sanitize_for_voice("") == ""

    def test_plain_text_unchanged(self):
        text = "السلام عليكم كيف الحال"
        result = sanitize_for_voice(text)
        assert result.strip() == text

    def test_converts_table_to_spoken(self):
        table = (
            "| الوثيقة | المكان |\n"
            "|---------|--------|\n"
            "| CIN | البلدية |\n"
            "| شهادة | المقاطعة |\n"
        )
        result = sanitize_for_voice(table, "darija")
        assert "أولاً" in result
        assert "ثانياً" in result
        assert "---|" not in result

    def test_converts_table_french(self):
        table = (
            "| Document | Lieu |\n"
            "|----------|------|\n"
            "| CIN | Commune |\n"
        )
        result = sanitize_for_voice(table, "fr")
        assert "Premièrement" in result

    def test_triple_bold_italic(self):
        result = sanitize_for_voice("***مهم جداً***")
        assert "***" not in result
        assert "مهم جداً" in result

    def test_nested_formatting(self):
        result = sanitize_for_voice("هذا **نص _مهم_ جداً**")
        assert "**" not in result
        assert "_" not in result


# ═══════════════════════════════════════════════════════════════════════════ #
#  _detect_language
# ═══════════════════════════════════════════════════════════════════════════ #

class TestDetectLanguage:
    """Tests for heuristic language detection."""

    def test_arabic_text(self):
        assert _detect_language("بغيت نعرف الوثائق") == "darija"

    def test_french_text(self):
        assert _detect_language("Je voudrais savoir les documents") == "fr"

    def test_mixed_defaults_darija(self):
        # Mostly Arabic with some French
        assert _detect_language("بغيت نعرف les documents ديالي") == "darija"

    def test_empty_defaults_darija(self):
        assert _detect_language("") == "darija"


# ═══════════════════════════════════════════════════════════════════════════ #
#  get_browser_voice_config
# ═══════════════════════════════════════════════════════════════════════════ #

class TestBrowserVoiceConfig:
    """Tests for browser Web Speech API configuration."""

    def test_darija_config(self):
        config = get_browser_voice_config("darija")
        assert config["tts"]["lang"] == "ar-MA"
        assert config["stt"]["lang"] == "ar-MA"
        assert "tts" in config
        assert "stt" in config

    def test_arabic_config(self):
        config = get_browser_voice_config("ar")
        assert config["tts"]["lang"] == "ar-SA"

    def test_french_config(self):
        config = get_browser_voice_config("fr")
        assert config["tts"]["lang"] == "fr-MA"

    def test_unknown_defaults_to_darija(self):
        config = get_browser_voice_config("unknown")
        assert config["tts"]["lang"] == "ar-MA"

    def test_has_fallback_langs(self):
        for lang in ["darija", "ar", "fr"]:
            config = get_browser_voice_config(lang)
            assert len(config["tts"]["fallbackLangs"]) >= 1
            assert len(config["stt"]["fallbackLangs"]) >= 1

    def test_rate_in_range(self):
        for lang in ["darija", "ar", "fr"]:
            config = get_browser_voice_config(lang)
            assert 0.5 <= config["tts"]["rate"] <= 2.0


# ═══════════════════════════════════════════════════════════════════════════ #
#  ALLOWED_AUDIO_MIMES
# ═══════════════════════════════════════════════════════════════════════════ #

class TestAllowedMimes:
    """Tests for supported audio MIME types."""

    def test_webm_supported(self):
        assert "audio/webm" in ALLOWED_AUDIO_MIMES

    def test_wav_supported(self):
        assert "audio/wav" in ALLOWED_AUDIO_MIMES

    def test_mp3_supported(self):
        assert "audio/mp3" in ALLOWED_AUDIO_MIMES

    def test_mpeg_supported(self):
        assert "audio/mpeg" in ALLOWED_AUDIO_MIMES

    def test_ogg_supported(self):
        assert "audio/ogg" in ALLOWED_AUDIO_MIMES

    def test_text_not_supported(self):
        assert "text/plain" not in ALLOWED_AUDIO_MIMES
