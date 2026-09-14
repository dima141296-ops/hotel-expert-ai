import json
from dataclasses import dataclass


class InvalidGeneratedContent(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedContent:
    expert_card: str
    telegram_post: str
    reels_script: str
    publication_package: str
    fact_check: str

    @classmethod
    def from_json(cls, raw: str) -> "GeneratedContent":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InvalidGeneratedContent(
                "AI вернул ответ не в формате JSON."
            ) from exc

        fields = (
            "expert_card",
            "telegram_post",
            "reels_script",
            "publication_package",
            "fact_check",
        )

        if not isinstance(data, dict) or any(
            not isinstance(data.get(field), str)
            or not data[field].strip()
            for field in fields
        ):
            raise InvalidGeneratedContent(
                "В ответе AI нет всех пяти обязательных разделов."
            )

        return cls(
            **{
                field: data[field].strip()
                for field in fields
            }
        )

    def as_sections(self) -> dict[str, str]:
        return {
            "Карточка для турагента": self.expert_card,
            "Пост для Telegram": self.telegram_post,
            "Сценарий Reels": self.reels_script,
            "Пакет публикации": self.publication_package,
            "Проверка фактов": self.fact_check,
        }
