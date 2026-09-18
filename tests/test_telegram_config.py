from app.telegram_config import load_telegram_settings


def test_load_settings_parses_allowed_user_ids():
    settings = load_telegram_settings(
        {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_ALLOWED_USER_IDS": "101, 202",
            "GEMINI_API_KEY": "test-key",
            "GEMINI_MODEL": "test-model",
        }
    )

    assert settings.allowed_user_ids == frozenset({101, 202})
import pytest

from app.telegram_config import TelegramConfigError


def test_load_settings_rejects_non_positive_user_id():
    with pytest.raises(
        TelegramConfigError,
        match="содержать числа через запятую",
    ):
        load_telegram_settings(
            {
                "TELEGRAM_BOT_TOKEN": "test-token",
                "TELEGRAM_ALLOWED_USER_IDS": "0",
                "GEMINI_API_KEY": "test-key",
                "GEMINI_MODEL": "test-model",
            }
        )
