import json

import pytest

from app.hotel_repository import HotelFileError, load_hotel


def test_load_hotel_reads_one_json_object(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(
        json.dumps(
            {
                "name": "Sea Breeze Hotel",
                "observations": ["Тихий двор"],
            }
        ),
        encoding="utf-8",
    )

    hotel = load_hotel(path)

    assert hotel.name == "Sea Breeze Hotel"


def test_load_hotel_rejects_json_array(tmp_path):
    path = tmp_path / "hotels.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(HotelFileError, match="одного отеля"):
        load_hotel(path)
