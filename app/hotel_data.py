from dataclasses import dataclass, field
from typing import Any


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [cleaned for item in value if (cleaned := _clean_text(item))]


@dataclass(frozen=True)
class HotelData:
    name: str
    city: str = ""
    district: str = ""
    inspection_date: str = ""
    representative_facts: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    suitable_for: list[str] = field(default_factory=list)
    filmed_shots: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    room_count: int | None = None
    last_renovation: str = ""
    sources: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "HotelData":
        raw_room_count = raw.get("room_count")
        room_count = raw_room_count if isinstance(raw_room_count, int) else None

        return cls(
            name=_clean_text(raw.get("name")),
            city=_clean_text(raw.get("city")),
            district=_clean_text(raw.get("district")),
            inspection_date=_clean_text(raw.get("inspection_date")),
            representative_facts=_clean_list(raw.get("representative_facts")),
            observations=_clean_list(raw.get("observations")),
            strengths=_clean_list(raw.get("strengths")),
            limitations=_clean_list(raw.get("limitations")),
            suitable_for=_clean_list(raw.get("suitable_for")),
            filmed_shots=_clean_list(raw.get("filmed_shots")),
            questions=_clean_list(raw.get("questions")),
            room_count=room_count,
            last_renovation=_clean_text(raw.get("last_renovation")),
            sources=_clean_list(raw.get("sources")),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.name:
            errors.append("Укажите название отеля.")

        if not (
            self.representative_facts
            or self.observations
            or self.strengths
            or self.limitations
            or self.filmed_shots
        ):
            errors.append(                "Добавьте хотя бы один факт или личное наблюдение."
            )

        return errors
