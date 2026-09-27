"""Timeout-safe adapter around Google's current ``google.genai`` SDK.

All Gemini integrations go through this module so network failures have one
bounded timeout and callers can reliably switch to deterministic fallbacks.
Business decisions remain in the calling services.
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types


logger = logging.getLogger(__name__)

GEMINI_TIMEOUT_SECONDS = 20
GEMINI_TIMEOUT_MS = GEMINI_TIMEOUT_SECONDS * 1000


class GeminiRequestError(RuntimeError):
    """Raised when Gemini is unavailable, times out, or returns no usable text."""


def binary_part(data: bytes, mime_type: str) -> types.Part:
    """Build a current-SDK binary part for audio, images, or PDFs."""
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def generate_text(
    *,
    api_key: str,
    model: str,
    contents: Any,
    system_instruction: str | None = None,
    temperature: float = 0.1,
    response_mime_type: str | None = None,
    safety_settings: list[types.SafetySetting] | None = None,
) -> str:
    """Generate text with an explicit 20-second HTTP timeout."""
    if not api_key.strip():
        raise GeminiRequestError("Gemini is not configured.")

    client: genai.Client | None = None
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type=response_mime_type,
            safety_settings=safety_settings,
            # Keep the timeout explicit at request and client level.
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        text = (response.text or "").strip()
        if not text:
            raise GeminiRequestError("Gemini returned no usable text.")
        return text
    except GeminiRequestError:
        raise
    except Exception as exc:
        logger.warning(
            "Gemini request failed (model=%s, timeout=%ss): %s",
            model,
            GEMINI_TIMEOUT_SECONDS,
            exc,
            exc_info=True,
        )
        raise GeminiRequestError("Gemini is temporarily unavailable.") from exc
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                logger.debug("Unable to close Gemini client cleanly", exc_info=True)
