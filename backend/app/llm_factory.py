"""LLM provider factory for the shared RAG pipeline."""
from __future__ import annotations

from typing import Any

from app.core.config import Settings, settings


SUPPORTED_LLM_PROVIDERS = ("ollama", "openai", "gemini")


class LLMConfigurationError(ValueError):
    """Raised when the selected LLM provider is missing required configuration."""


def create_llm(config: Settings = settings) -> Any:
    """Create the LlamaIndex LLM selected by server-side environment settings."""
    provider = config.llm_provider.strip().lower()

    if provider == "ollama":
        from llama_index.llms.ollama import Ollama

        print("[OK] LLM provider: ollama")
        return Ollama(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
            request_timeout=config.ollama_request_timeout,
            context_window=config.ollama_context_window,
            temperature=0.1,
        )

    if provider == "openai":
        if not config.openai_api_key:
            print("[WARN] OPENAI_API_KEY missing")
            raise LLMConfigurationError("OPENAI_API_KEY is required for LLM_PROVIDER=openai")

        from llama_index.llms.openai import OpenAI

        print("[OK] LLM provider: openai")
        return OpenAI(
            model=config.openai_model,
            api_key=config.openai_api_key,
            temperature=0.1,
        )

    if provider == "gemini":
        if not config.google_api_key:
            print("[WARN] GOOGLE_API_KEY missing")
            raise LLMConfigurationError("GOOGLE_API_KEY is required for LLM_PROVIDER=gemini")

        from llama_index.llms.google_genai import GoogleGenAI

        print("[OK] LLM provider: gemini")
        return GoogleGenAI(
            model=config.gemini_model,
            api_key=config.google_api_key,
            temperature=0.1,
        )

    supported = ", ".join(SUPPORTED_LLM_PROVIDERS)
    print(f"[WARN] Unsupported LLM_PROVIDER: {provider or '<empty>'}")
    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER '{provider}'. Expected one of: {supported}"
    )
