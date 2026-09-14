import json

import pytest

from app.generated_content import (
    GeneratedContent,
    InvalidGeneratedContent,
)


def test_generated_content_parses_five_sections():
    raw = json.dumps(
        {
            "expert_card": "Карточка",
            "telegram_post": "Пост",
            "reels_script": "Сценарий",
            "publication_package": "Пакет",
            "fact_check": "Проверка",
        }
    )

    content = GeneratedContent.from_json(raw)

    assert content.telegram_post == "Пост"
    assert len(content.as_sections()) == 5


def test_generated_content_rejects_missing_section():
    with pytest.raises(
        InvalidGeneratedContent,
        match="обязательных разделов",
    ):
        GeneratedContent.from_json(
            '{"expert_card": "Карточка"}'
        )
