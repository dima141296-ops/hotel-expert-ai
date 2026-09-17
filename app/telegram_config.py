from dataclasses import dataclass
from typing import Mapping


class TelegramConfigError(ValueError):
    pass


@dataclass(frozen=True)
class TelegramSettings:
    bot_token: str
    allowed_user_ids: frozenset[int]
    gemini_api_key: str
    gemini_model: str

    def is_allowed(self, user_id: int) -> bool:
        return user_id in self.allowed_user_ids


def load_telegram_settings(
    env: Mapping[str, str],
) -> TelegramSettings:
    bot_token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        raise TelegramConfigError(
            "Не задан TELEGRAM_BOT_TOKEN "
            "в локальном файле .env."
        )

    raw_allowed_ids = env.get(
        "TELEGRAM_ALLOWED_USER_IDS",
        "",
    ).strip()
    if not raw_allowed_ids:
        raise TelegramConfigError(
            "Не задан TELEGRAM_ALLOWED_USER_IDS "
            "в локальном файле .env."
        )

    try:
        parsed_ids = [
            int(item.strip())
            for item in raw_allowed_ids.split(",")
        ]

        if any(user_id <= 0 for user_id in parsed_ids):
            raise ValueError

        allowed_user_ids = frozenset(parsed_ids)
    except ValueError as exc:
        raise TelegramConfigError(
            "TELEGRAM_ALLOWED_USER_IDS должен "
            "содержать числа через запятую."
        ) from exc

    gemini_api_key = env.get("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise TelegramConfigError(
            "Не задан GEMINI_API_KEY "
            "в локальном файле .env."
        )

    gemini_model = env.get("GEMINI_MODEL", "").strip()
    if not gemini_model:
        raise TelegramConfigError(
            "Не задан GEMINI_MODEL "
            "в локальном файле .env."
        )

    return TelegramSettings(
        bot_token=bot_token,
        allowed_user_ids=allowed_user_ids,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )
