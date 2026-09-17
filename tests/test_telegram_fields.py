import pytest

from app.telegram_fields import (
    answers_to_hotel,
    parse_list_text,
    parse_room_count,
    split_telegram_text,
)


def test_parse_list_text_strips_blank_lines():
    result = parse_list_text(
        "  Бассейн  \n\nНомер Superior\n  "
    )

    assert result == [
        "Бассейн",
        "Номер Superior",
    ]


def test_parse_room_count_accepts_positive_number():
    assert parse_room_count("864") == 864


def test_parse_room_count_rejects_zero():
    with pytest.raises(
        ValueError,
        match="положительным",
    ):
        parse_room_count("0")


def test_answers_to_hotel_uses_existing_model():
    hotel = answers_to_hotel(
        {
            "name": "Test Hotel",
            "observations": ["Тихо"],
            "room_count": 100,
        }
    )

    assert hotel.name == "Test Hotel"
    assert hotel.observations == ["Тихо"]
    assert hotel.room_count == 100


def test_split_telegram_text_keeps_limit_and_text():
    text = "А" * 5000

    chunks = split_telegram_text(text)

    assert all(len(chunk) <= 4096 for chunk in chunks)
    assert "".join(chunks) == text
