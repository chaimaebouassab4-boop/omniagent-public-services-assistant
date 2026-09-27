"""Tests for the bounded google.genai adapter."""

from types import SimpleNamespace

import pytest

from app.services import gemini_client


def test_generate_text_applies_20_second_timeout(monkeypatch):
    captured = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured["request"] = kwargs
            return SimpleNamespace(text="  réponse  ")

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.models = FakeModels()

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)

    result = gemini_client.generate_text(
        api_key="test-key",
        model="test-model",
        contents="bonjour",
    )

    assert result == "réponse"
    assert captured["client"]["http_options"].timeout == 20_000
    assert captured["request"]["config"].http_options.timeout == 20_000
    assert captured["closed"] is True


def test_generate_text_wraps_provider_errors(monkeypatch):
    class FailingClient:
        def __init__(self, **kwargs):
            raise TimeoutError("network timeout")

    monkeypatch.setattr(gemini_client.genai, "Client", FailingClient)

    with pytest.raises(gemini_client.GeminiRequestError, match="temporarily unavailable"):
        gemini_client.generate_text(
            api_key="test-key",
            model="test-model",
            contents="bonjour",
        )
