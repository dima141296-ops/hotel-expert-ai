import json

import pytest

from app.ai_provider import AIProviderError
from app.content_generator import (
    ContentGenerationError,
    ContentGenerator,
)
from app.hotel_data import HotelData


class FakeProvider:
    def generate(self, prompt: str) -> str:
        assert "Test Hotel" in prompt

        return json.dumps(
            {
                "expert_card": "Карточка",
                "telegram_post": "Пост",
                "reels_script": "Сценарий",
                "publication_package": "Пакет",
                "fact_check": "Проверка",
            }
        )


class BrokenProvider:
    def generate(self, prompt: str) -> str:
        raise AIProviderError(
            "Сервис временно недоступен."
        )


def test_generator_uses_shared_prompt_and_returns_content():
    hotel = HotelData.from_dict(
        {
            "name": "Test Hotel",
            "observations": ["Тихо"],
        }
    )

    result = ContentGenerator(
        FakeProvider()
    ).generate(hotel)

    assert result.expert_card == "Карточка"


def test_generator_returns_clear_error_when_provider_fails():
    hotel = HotelData.from_dict(
        {
            "name": "Test Hotel",
            "observations": ["Тихо"],
        }
    )

    with pytest.raises(
        ContentGenerationError,
        match="Повторите попытку",
    ):
        ContentGenerator(
            BrokenProvider()
        ).generate(hotel)
