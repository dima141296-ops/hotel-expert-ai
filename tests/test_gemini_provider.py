from types import SimpleNamespace

import pytest

from app.ai_provider import AIProviderError
from app.gemini_provider import GeminiProvider


class FakeModels:
    def generate_content(
        self,
        *,
        model,
        contents,
        config,
    ):
        assert model == "test-model"
        assert "Test Hotel" in contents
        assert (
            config["response_mime_type"]
            == "application/json"
        )

        return SimpleNamespace(
            text='{"expert_card":"A"}'
        )


class FakeClient:
    models = FakeModels()


def test_gemini_provider_returns_response_text():
    provider = GeminiProvider(
        "secret",
        "test-model",
        client=FakeClient(),
    )

    assert (
        provider.generate("Test Hotel")
        == '{"expert_card":"A"}'
    )


def test_gemini_provider_requires_key():
    with pytest.raises(
        AIProviderError,
        match="GEMINI_API_KEY",
    ):
        GeminiProvider("", "test-model")
