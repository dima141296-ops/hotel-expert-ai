from dataclasses import dataclass
from typing import Mapping

from app.hotel_data import HotelData


@dataclass(frozen=True)
class HotelField:
    key: str
    question: str
    kind: str
    optional: bool


HOTEL_FIELDS = (
    HotelField(
        "name",
        "Как называется отель?",
        "text",
        False,
    ),
    HotelField(
        "city",
        "В каком городе находится отель? "
        "Или отправьте /skip.",
        "text",
        True,
    ),
    HotelField(
        "district",
        "Укажите район. Или отправьте /skip.",
        "text",
        True,
    ),
    HotelField(
        "inspection_date",
        "Укажите дату инспекции. Или отправьте /skip.",
        "text",
        True,
    ),
    HotelField(
        "representative_facts",
        "Введите подтверждённые факты: "
        "каждый с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "observations",
        "Введите личные наблюдения: "
        "каждое с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "strengths",
        "Введите сильные стороны: "
        "каждую с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "limitations",
        "Введите ограничения: "
        "каждое с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "suitable_for",
        "Кому подходит отель? "
        "Каждый вариант с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "filmed_shots",
        "Какие кадры сняты? "
        "Каждый вариант с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "questions",
        "Какие вопросы нужно уточнить? "
        "Каждый с новой строки. Или /skip.",
        "list",
        True,
    ),
    HotelField(
        "room_count",
        "Укажите число номеров целым числом. "
        "Или /skip.",
        "room_count",
        True,
    ),
    HotelField(
        "last_renovation",
        "Укажите последнюю реновацию. Или /skip.",
        "text",
        True,
    ),
    HotelField(
        "sources",
        "Укажите источники: "
        "каждый с новой строки. Или /skip.",
        "list",
        True,
    ),
)


def parse_list_text(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def parse_room_count(text: str) -> int:
    try:
        room_count = int(text.strip())
    except ValueError as exc:
        raise ValueError(
            "Число номеров должно быть "
            "положительным целым числом."
        ) from exc

    if room_count <= 0:
        raise ValueError(
            "Число номеров должно быть "
            "положительным целым числом."
        )

    return room_count


def parse_field_value(
    field: HotelField,
    text: str,
) -> str | int | list[str]:
    if field.kind == "list":
        return parse_list_text(text)

    if field.kind == "room_count":
        return parse_room_count(text)

    return text.strip()


def empty_field_value(
    field: HotelField,
) -> str | None | list[str]:
    if field.kind == "list":
        return []

    if field.kind == "room_count":
        return None

    return ""


def answers_to_hotel(
    answers: Mapping[str, object],
) -> HotelData:
    return HotelData.from_dict(dict(answers))


def split_telegram_text(
    text: str,
    limit: int = 4096,
) -> list[str]:
    if not text:
        return []

    chunks: list[str] = []
    remaining = text

    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit + 1)

        if split_at > 0:
            split_at += 1
        else:
            split_at = limit

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]

    chunks.append(remaining)

    return chunks
