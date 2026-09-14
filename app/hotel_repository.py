import json
from pathlib import Path

from app.hotel_data import HotelData


class HotelFileError(ValueError):
    pass


def load_hotel(path: str | Path) -> HotelData:
    file_path = Path(path)

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HotelFileError(
            "Не удалось прочитать файл отеля."
        ) from exc

    if not isinstance(raw, dict):
        raise HotelFileError(
            "Файл должен содержать данные одного отеля."
        )

    return HotelData.from_dict(raw)
