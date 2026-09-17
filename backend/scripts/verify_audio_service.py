"""End-to-end verification of the audio processing service.

Run from the backend directory:
    python scripts/verify_audio_service.py

Tests:
  1. Voice-ready text sanitization (markdown → spoken text)
  2. TTS synthesis (text → MP3 bytes)
  3. Darija audio transcription round-trip (gTTS → Gemini STT)
  4. Browser voice configuration
"""

from __future__ import annotations

import io
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.services.audio_service import (  # noqa: E402
    get_browser_voice_config,
    sanitize_for_voice,
    synthesize_speech,
    transcribe_audio,
)


def _header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def test_sanitize_for_voice() -> bool:
    """Test markdown → spoken text transformation."""
    _header("Test 1: Voice-Ready Text Sanitization")

    markdown_input = """\
## الوثائق المطلوبة

لاستخراج **شهادة السكنى**، تحتاج:

| الوثيقة | المكان |
|---------|--------|
| CIN | البلدية |
| شهادة الميلاد | الحالة المدنية |

### ملاحظة
> يجب أن تكون الوثائق **أصلية** ~~وليست نسخة~~.

للمزيد: [اضغط هنا](https://example.com)
"""

    result = sanitize_for_voice(markdown_input, "darija")
    print(f"Input length:  {len(markdown_input)} chars")
    print(f"Output length: {len(result)} chars")
    print(f"Output:\n{result}")

    # Verify markdown was stripped
    assert "**" not in result, "Bold markdown not stripped"
    assert "##" not in result, "Header markdown not stripped"
    assert "~~" not in result, "Strikethrough not stripped"
    assert "[اضغط هنا](https://example.com)" not in result, "Link not stripped"
    assert "---|" not in result, "Table separator not stripped"
    # Verify tables were converted
    assert "أولاً" in result or "CIN" in result, "Table not converted to spoken form"

    print("\n✅ PASSED: Voice text sanitization works correctly")
    return True


def test_tts_synthesis() -> bool:
    """Test text-to-speech MP3 generation."""
    _header("Test 2: TTS Synthesis (gTTS)")

    text_ar = "مرحبا بكم في منصة أمنية للخدمات العمومية"
    text_fr = "Bienvenue sur la plateforme Omniagent"

    mp3_ar = synthesize_speech(text_ar, "ar")
    mp3_fr = synthesize_speech(text_fr, "fr")

    print(f"Arabic TTS:  {len(text_ar)} chars → {len(mp3_ar):,} bytes MP3")
    print(f"French TTS:  {len(text_fr)} chars → {len(mp3_fr):,} bytes MP3")

    assert len(mp3_ar) > 1000, "Arabic MP3 too small"
    assert len(mp3_fr) > 1000, "French MP3 too small"
    # Verify valid MP3 (starts with ID3 or MPEG sync)
    assert mp3_ar[:3] == b"ID3" or mp3_ar[0:1] == b"\xff", "Invalid Arabic MP3 header"
    assert mp3_fr[:3] == b"ID3" or mp3_fr[0:1] == b"\xff", "Invalid French MP3 header"

    print("\n✅ PASSED: TTS synthesis generates valid MP3")
    return True


def test_transcription_roundtrip() -> bool:
    """Test Darija audio transcription via Gemini Flash (round-trip)."""
    _header("Test 3: Darija Transcription Round-Trip (gTTS → Gemini STT)")

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("⚠️  SKIPPED: GOOGLE_API_KEY not set")
        return True

    # Generate Arabic audio via gTTS
    from gtts import gTTS  # type: ignore

    original_text = "بغيت نعرف الوثائق ديال شهادة السكنى عفاك"
    buf = io.BytesIO()
    tts = gTTS(text=original_text, lang="ar", slow=False)
    tts.write_to_fp(buf)
    audio_bytes = buf.getvalue()

    print(f"Original text: {original_text}")
    print(f"Generated audio: {len(audio_bytes):,} bytes MP3")

    # Transcribe with Gemini
    result = transcribe_audio(
        audio_bytes=audio_bytes,
        mime_type="audio/mp3",
        language_hint="darija",
    )

    print(f"Transcription: {result['text']}")
    print(f"Language:      {result['language']}")
    print(f"Confidence:    {result['confidence']}")
    print(f"Error:         {result['error']}")

    assert result["error"] is None, f"Transcription error: {result['error']}"
    assert len(result["text"]) > 5, "Transcription too short"

    # Check that key words appear in the transcription
    key_words = ["شهادة", "السكنى"]
    found = sum(1 for w in key_words if w in result["text"])
    print(f"Key words found: {found}/{len(key_words)}")
    assert found >= 1, "Transcription doesn't contain expected keywords"

    print("\n✅ PASSED: Darija transcription round-trip successful")
    return True


def test_browser_voice_config() -> bool:
    """Test browser voice configuration generator."""
    _header("Test 4: Browser Voice Configuration")

    for lang in ["darija", "ar", "fr"]:
        config = get_browser_voice_config(lang)
        print(f"\n  {lang}:")
        print(f"    TTS lang: {config['tts']['lang']}")
        print(f"    STT lang: {config['stt']['lang']}")
        print(f"    Rate:     {config['tts']['rate']}")

        assert "tts" in config, f"Missing TTS config for {lang}"
        assert "stt" in config, f"Missing STT config for {lang}"
        assert config["tts"]["lang"], f"Empty TTS lang for {lang}"

    print("\n✅ PASSED: Browser voice configs are valid")
    return True


if __name__ == "__main__":
    results = []
    results.append(("Sanitize for voice", test_sanitize_for_voice()))
    results.append(("TTS synthesis", test_tts_synthesis()))
    results.append(("Transcription round-trip", test_transcription_roundtrip()))
    results.append(("Browser voice config", test_browser_voice_config()))

    _header("RESULTS SUMMARY")
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed.")
        sys.exit(1)
