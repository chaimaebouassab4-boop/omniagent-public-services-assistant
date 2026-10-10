"""Timeout-safe adapter around Google's current ``google.genai`` SDK.

All Gemini integrations go through this module so network failures have one
bounded timeout and callers can reliably switch to deterministic fallbacks.
Business decisions remain in the calling services.
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import errors, types


logger = logging.getLogger(__name__)

GEMINI_TIMEOUT_SECONDS = 20
GEMINI_TIMEOUT_MS = GEMINI_TIMEOUT_SECONDS * 1000


class GeminiRequestError(RuntimeError):
    """Raised when Gemini is unavailable, times out, or returns no usable text."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "gemini_request_failed",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.status_code = status_code


def _provider_failure_reason(status_code: int | None) -> str:
    if status_code == 429:
        return "gemini_rate_limited_http_429"
    if status_code == 503:
        return "gemini_service_unavailable_http_503"
    if status_code is not None and status_code >= 500:
        return "gemini_provider_server_error"
    return "gemini_request_failed"


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
        raise GeminiRequestError(
            "Gemini is not configured.",
            reason="gemini_not_configured",
        )

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
            # OmniAgent sends no tools and does not use function calling.
            # google-genai enables its AFC wrapper by default unless disabled.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
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
            raise GeminiRequestError(
                "Gemini returned no usable text.",
                reason="gemini_empty_response",
            )
        return text
    except GeminiRequestError:
        raise
    except errors.APIError as exc:
        # Provider HTTP failures are expected operational conditions. Keep
        # payloads and tracebacks out of normal terminal output.
        raise GeminiRequestError(
            "Gemini is temporarily unavailable.",
            reason=_provider_failure_reason(exc.code),
            status_code=exc.code,
        ) from exc
    except Exception as exc:
        # Programming/integration failures are unexpected and retain a proper
        # traceback, without logging prompts, contents, credentials or payloads.
        logger.exception(
            "Unexpected Gemini client failure (model=%s, timeout=%ss, type=%s)",
            model,
            GEMINI_TIMEOUT_SECONDS,
            type(exc).__name__,
        )
        raise GeminiRequestError(
            "Gemini is temporarily unavailable.",
            reason="gemini_client_error",
        ) from exc
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                logger.debug("Unable to close Gemini client cleanly", exc_info=True)
