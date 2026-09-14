from app.hotel_data import HotelData


def test_from_dict_strips_text_and_keeps_lists():
    hotel = HotelData.from_dict(
        {
            "name": "  Long Beach Garden Hotel  ",
            "city": "Паттайя",
            "district": "Вонгамат",
            "inspection_date": "11.06.2026",
            "representative_facts": ["864 номера", "Три корпуса"],
            "observations": ["Номера выглядят уставшими"],
            "strengths": ["Первая береговая линия"],
            "limitations": ["К пляжу ведут ступеньки"],
            "suitable_for": ["Семьи с детьми"],
            "filmed_shots": ["Бассейн", "Номер Superior"],
            "questions": ["Когда будет реновация?"],
            "room_count": 864,
            "last_renovation": "2014",
            "sources": ["Представитель отеля", "Личный осмотр"],
        }
    )

    assert hotel.name == "Long Beach Garden Hotel"
    assert hotel.city == "Паттайя"
    assert hotel.district == "Вонгамат"
    assert hotel.inspection_date == "11.06.2026"
    assert hotel.representative_facts == ["864 номера", "Три корпуса"]
    assert hotel.observations == ["Номера выглядят уставшими"]
    assert hotel.strengths == ["Первая береговая линия"]
    assert hotel.limitations == ["К пляжу ведут ступеньки"]
    assert hotel.suitable_for == ["Семьи с детьми"]
    assert hotel.filmed_shots == ["Бассейн", "Номер Superior"]
    assert hotel.questions == ["Когда будет реновация?"]
    assert hotel.room_count == 864
    assert hotel.last_renovation == "2014"
    assert hotel.sources == ["Представитель отеля", "Личный осмотр"]


def test_validate_requires_name():
    hotel = HotelData.from_dict(
        {"name": "", "observations": ["Тихая территория"]}
    )

    assert "Укажите название отеля." in hotel.validate()


def test_validate_requires_at_least_one_meaningful_fact():
    hotel = HotelData.from_dict({"name": "Test Hotel"})

    assert (
        "Добавьте хотя бы один факт или личное наблюдение."
        in hotel.validate()
    )


def test_empty_optional_values_do_not_become_invented_text():
    hotel = HotelData.from_dict(
        {
            "name": "Test Hotel",
            "strengths": ["  Хороший пляж  ", ""],
        }
    )

    assert hotel.strengths == ["Хороший пляж"]
    assert hotel.city == ""


def test_strengths_count_as_meaningful_facts():
    hotel = HotelData.from_dict(
        {"name": "Test Hotel", "strengths": ["Хороший пляж"]}
    )

    assert hotel.validate() == []


def test_other_fact_categories_count_as_meaningful_facts():
    for field_name in (
        "representative_facts",
        "limitations",
        "filmed_shots",
    ):
        hotel = HotelData.from_dict(
            {"name": "Test Hotel", field_name: ["Подтверждённая деталь"]}
        )

        assert hotel.validate() == [], field_name
