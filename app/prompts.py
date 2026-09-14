from app.hotel_data import HotelData


class InvalidHotelData(ValueError):
    pass


def _bullets(values: list[str]) -> str:
    if not values:
        return "- Не указано"

    return "\n".join(f"- {value}" for value in values)


def build_expert_prompt(hotel: HotelData) -> str:
    errors = hotel.validate()

    if errors:
        raise InvalidHotelData(" ".join(errors))

    return f"""Ты — редактор экспертного контента об отелях для русскоязычных турагентов.
Используй только сведения ниже. Не добавляй цены, расстояния, услуги, оценки или обещания, которых нет во входных данных.
Разделяй подтверждённые сведения и личные наблюдения. Неизвестное помечай как «Нужно уточнить».
Тон: профессиональный, спокойный, конкретный, без рекламных клише.

Название: {hotel.name}
Город: {hotel.city or 'Не указано'}
Район: {hotel.district or 'Не указано'}
Дата инспекции: {hotel.inspection_date or 'Не указано'}
Количество номеров: {hotel.room_count if hotel.room_count is not None else 'Не указано'}
Последняя реновация: {hotel.last_renovation or 'Не указано'}

Факты от представителя:
{_bullets(hotel.representative_facts)}

Личные наблюдения Дмитрия:
{_bullets(hotel.observations)}

Сильные стороны:
{_bullets(hotel.strengths)}

Ограничения и нюансы:
{_bullets(hotel.limitations)}

Кому подходит:
{_bullets(hotel.suitable_for)}

Точно снятые кадры:
{_bullets(hotel.filmed_shots)}

Что требуется уточнить:
{_bullets(hotel.questions)}

Источники:
{_bullets(hotel.sources)}

Верни JSON-объект ровно с пятью строковыми полями:
1. expert_card
2. telegram_post
3. reels_script
4. publication_package
5. fact_check
"""
