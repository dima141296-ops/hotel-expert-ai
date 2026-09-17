from app.telegram_bot import is_allowed_user
from app.telegram_config import TelegramSettings


def test_is_allowed_user_checks_allowed_ids():
    settings = TelegramSettings(
        bot_token="test-token",
        allowed_user_ids=frozenset({101}),
        gemini_api_key="test-key",
        gemini_model="test-model",
    )

    assert is_allowed_user(101, settings)
    assert not is_allowed_user(202, settings)
    assert not is_allowed_user(None, settings)
