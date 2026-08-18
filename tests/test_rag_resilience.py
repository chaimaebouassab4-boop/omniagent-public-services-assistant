"""Tests for chat prompt memory and provider rate-limit recognition."""
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.rag_service import OmniAgentRAG, _format_conversation_history, _is_rate_limit_error, _prompt_with_history


def test_history_is_limited_to_five_exchanges():
    history = [
        {"role": "user" if index % 2 == 0 else "assistant", "content": f"message-{index}"}
        for index in range(14)
    ]
    rendered = _format_conversation_history(history)
    assert "message-3" not in rendered
    assert "message-4" in rendered
    assert "message-13" in rendered


def test_history_is_added_to_prompt_without_replacing_query_variable():
    prompt = _prompt_with_history([{"role": "user", "content": "And the price?"}])
    assert "User: And the price?" in prompt
    assert "{context_str}" in prompt
    assert "{query_str}" in prompt


def test_nested_http_429_is_recognized():
    inner = RuntimeError("429 RESOURCE_EXHAUSTED")
    outer = RuntimeError("Gemini request failed")
    outer.__cause__ = inner
    assert _is_rate_limit_error(outer)


def test_unrelated_provider_error_is_not_a_rate_limit():
    assert not _is_rate_limit_error(RuntimeError("connection refused"))


def test_http_429_query_uses_local_kb_fallback():
    class RateLimitError(RuntimeError):
        status_code = 429

    query_engine = MagicMock()
    query_engine.query.side_effect = RateLimitError("quota exhausted")
    index = MagicMock()
    index.as_query_engine.return_value = query_engine

    engine = OmniAgentRAG.__new__(OmniAgentRAG)
    engine.initialized = True
    engine.index = index
    engine.qa_prompt = object()
    engine._fallback_query = MagicMock(return_value={"answer": "local answer"})

    llama_index = ModuleType("llama_index")
    llama_index.__path__ = []
    core = ModuleType("llama_index.core")
    core.__path__ = []
    core.PromptTemplate = lambda template: template
    vector_stores = ModuleType("llama_index.core.vector_stores")
    vector_stores.MetadataFilters = lambda **kwargs: kwargs
    vector_stores.ExactMatchFilter = lambda **kwargs: kwargs

    with patch.dict(
        sys.modules,
        {
            "llama_index": llama_index,
            "llama_index.core": core,
            "llama_index.core.vector_stores": vector_stores,
        },
    ):
        result = engine.query("question", "residence")

    assert result == {"answer": "local answer"}
    reason = engine._fallback_query.call_args.kwargs["reason"]
    assert "HTTP 429" in reason
