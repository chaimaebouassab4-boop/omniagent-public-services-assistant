"""Unit tests for provider selection; no network or model calls are made."""
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.config import Settings
from app.llm_factory import LLMConfigurationError, create_llm


@pytest.mark.parametrize(
    ("provider", "module_name", "class_name", "model_field", "model"),
    [
        ("ollama", "llama_index.llms.ollama", "Ollama", "ollama_model", "local-model"),
        ("openai", "llama_index.llms.openai", "OpenAI", "openai_model", "openai-model"),
        ("gemini", "llama_index.llms.google_genai", "GoogleGenAI", "gemini_model", "gemini-model"),
    ],
)
def test_create_llm_selects_provider(provider, module_name, class_name, model_field, model):
    constructor = MagicMock(return_value=object())
    provider_module = ModuleType(module_name)
    setattr(provider_module, class_name, constructor)
    config_values = {
        "llm_provider": provider,
        model_field: model,
        "openai_api_key": "test-openai-key",
        "google_api_key": "test-google-key",
    }
    config = Settings(_env_file=None, **config_values)

    # The provider packages are optional at unit-test time; production installs
    # all three integrations from backend/requirements.txt.
    with patch.dict(sys.modules, {module_name: provider_module}):
        created = create_llm(config)

    assert created is constructor.return_value
    assert constructor.call_args.kwargs["model"] == model


def test_default_provider_is_ollama():
    assert Settings(_env_file=None).llm_provider == "ollama"


@pytest.mark.parametrize(
    "config_values",
    [
        {"llm_provider": "openai", "openai_api_key": ""},
        {"llm_provider": "gemini", "google_api_key": ""},
        {"llm_provider": "unknown"},
    ],
)
def test_invalid_configuration_raises_controlled_error(config_values):
    with pytest.raises(LLMConfigurationError):
        create_llm(Settings(_env_file=None, **config_values))
