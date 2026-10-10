"""Regression coverage for the retired legacy LLM factory module."""
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app import llm_factory


def test_legacy_llm_factory_is_explicitly_deprecated():
    assert "DEPRECATED" in (llm_factory.__doc__ or "")
    assert "rag_service.py" in (llm_factory.__doc__ or "")
    assert not hasattr(llm_factory, "create_llm")
