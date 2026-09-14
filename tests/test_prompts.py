import pytest

from app.hotel_data import HotelData
from app.prompts import InvalidHotelData, build_expert_prompt


def test_prompt_separates_sources_and_requests_five_sections():
    hotel = HotelData.from_dict(
        {
            "name": "Test Hotel",
            "representative_facts": ["100 номеров"],
            "observations": ["В номере тихо"],
            "questions": ["Год реновации?"],
        }
    )

    prompt = build_expert_prompt(hotel)

    assert "Факты от представителя:\n- 100 номеров" in prompt
    assert "Личные наблюдения Дмитрия:\n- В номере тихо" in prompt
    assert "Что требуется уточнить:\n- Год реновации?" in prompt
    assert "1. expert_card" in prompt
    assert "5. fact_check" in prompt


def test_prompt_rejects_invalid_hotel():
    with pytest.raises(InvalidHotelData, match="Укажите название"):
        build_expert_prompt(HotelData.from_dict({}))
