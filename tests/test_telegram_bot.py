import asyncio
from types import SimpleNamespace

import pytest
from telegram.ext import (
    ApplicationHandlerStop,
    ConversationHandler,
    TypeHandler,
)

from app.content_generator import ContentGenerationError
from app.generated_content import GeneratedContent
from app.telegram_bot import (
    ANSWERS_KEY,
    COLLECTING,
    CREATE_CONTENT,
    FIELD_INDEX_KEY,
    REVIEWING,
    block_disallowed_update,
    build_application,
    cancel,
    is_allowed_user,
    is_private_allowed_user,
    new_inspection,
    receive_value,
    review_callback,
    skip_field,
)
from app.telegram_config import TelegramSettings
from app.telegram_fields import HOTEL_FIELDS


class FakeMessage:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(
        self,
        text: str,
        reply_markup=None,
    ) -> None:
        self.replies.append(text)


class FakeQuery:
    def __init__(self, data: str) -> None:
        self.data = data
        self.answered = False

    async def answer(
        self,
        text=None,
        show_alert=False,
    ) -> None:
        self.answered = True


class SuccessfulGenerator:
    def generate(
        self,
        hotel,
    ) -> GeneratedContent:
        return GeneratedContent(
            expert_card="Карточка",
            telegram_post="Пост",
            reels_script="Сценарий",
            publication_package="Пакет",
            fact_check="Проверка",
        )


class BrokenGenerator:
    def generate(self, hotel) -> GeneratedContent:
        raise ContentGenerationError(
            "Не удалось получить ответ AI."
        )


def make_settings() -> TelegramSettings:
    return TelegramSettings(
        bot_token="test-token",
        allowed_user_ids=frozenset({101}),
        gemini_api_key="test-key",
        gemini_model="test-model",
    )


def make_context(
    generator=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "settings": make_settings(),
                "generator": generator,
            }
        ),
        user_data={},
    )


def make_update(
    *,
    text: str = "",
    user_id: int = 101,
    chat_type: str = "private",
    callback_data: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_chat=SimpleNamespace(type=chat_type),
        effective_message=FakeMessage(text),
        callback_query=(
            FakeQuery(callback_data)
            if callback_data
            else None
        ),
    )


def field_index(key: str) -> int:
    return next(
        index
        for index, field in enumerate(HOTEL_FIELDS)
        if field.key == key
    )


def test_is_allowed_user_checks_allowed_ids():
    settings = make_settings()

    assert is_allowed_user(101, settings)
    assert not is_allowed_user(202, settings)
    assert not is_allowed_user(None, settings)


def test_is_private_allowed_user_rejects_group_chat():
    settings = make_settings()

    assert is_private_allowed_user(
        101,
        "private",
        settings,
    )
    assert not is_private_allowed_user(
        101,
        "group",
        settings,
    )


def test_global_guard_stops_group_chat_before_dialog():
    update = make_update(chat_type="group")

    with pytest.raises(ApplicationHandlerStop):
        asyncio.run(
            block_disallowed_update(
                update,
                make_context(),
            )
        )

    assert update.effective_message.replies == [
        "Доступ к этому боту закрыт."
    ]


def test_new_inspection_starts_with_hotel_name():
    update = make_update()
    context = make_context()

    result = asyncio.run(
        new_inspection(update, context)
    )

    assert result == COLLECTING
    assert context.user_data[ANSWERS_KEY] == {}
    assert context.user_data[FIELD_INDEX_KEY] == 0
    assert (
        update.effective_message.replies[-1]
        == "Как называется отель?"
    )


def test_skip_moves_to_next_optional_field():
    update = make_update()
    context = make_context()
    context.user_data = {
        ANSWERS_KEY: {},
        FIELD_INDEX_KEY: field_index("city"),
    }

    result = asyncio.run(
        skip_field(update, context)
    )

    assert result == COLLECTING
    assert context.user_data[ANSWERS_KEY]["city"] == ""
    assert (
        context.user_data[FIELD_INDEX_KEY]
        == field_index("district")
    )


def test_cancel_clears_dialog_data():
    update = make_update()
    context = make_context()
    context.user_data = {
        ANSWERS_KEY: {"name": "Test Hotel"},
        FIELD_INDEX_KEY: 1,
    }

    result = asyncio.run(cancel(update, context))

    assert result == ConversationHandler.END
    assert context.user_data == {}


def test_invalid_room_count_repeats_same_field():
    update = make_update(text="ноль")
    context = make_context()
    room_count_index = field_index("room_count")
    context.user_data = {
        ANSWERS_KEY: {},
        FIELD_INDEX_KEY: room_count_index,
    }

    result = asyncio.run(
        receive_value(update, context)
    )

    assert result == COLLECTING
    assert context.user_data[FIELD_INDEX_KEY] == (
        room_count_index
    )
    assert "положительным" in (
        update.effective_message.replies[-1]
    )


def test_missing_facts_returns_to_facts_field():
    update = make_update()
    context = make_context()
    context.user_data = {
        ANSWERS_KEY: {"name": "Test Hotel"},
        FIELD_INDEX_KEY: field_index("sources"),
    }

    result = asyncio.run(
        skip_field(update, context)
    )

    assert result == COLLECTING
    assert context.user_data[FIELD_INDEX_KEY] == (
        field_index("representative_facts")
    )
    assert "Добавьте хотя бы один факт" in (
        update.effective_message.replies[-2]
    )


def test_generation_sends_five_sections():
    update = make_update(callback_data=CREATE_CONTENT)
    context = make_context(SuccessfulGenerator())
    context.user_data = {
        ANSWERS_KEY: {
            "name": "Test Hotel",
            "representative_facts": ["Бассейн"],
        },
        FIELD_INDEX_KEY: field_index("sources"),
    }

    result = asyncio.run(
        review_callback(update, context)
    )

    section_messages = [
        reply
        for reply in update.effective_message.replies
        if reply.startswith("## ")
    ]

    assert result == ConversationHandler.END
    assert len(section_messages) == 5
    assert context.user_data == {}


def test_generation_error_keeps_dialog_data():
    update = make_update(callback_data=CREATE_CONTENT)
    context = make_context(BrokenGenerator())
    context.user_data = {
        ANSWERS_KEY: {
            "name": "Test Hotel",
            "representative_facts": ["Бассейн"],
        },
        FIELD_INDEX_KEY: field_index("sources"),
    }

    result = asyncio.run(
        review_callback(update, context)
    )

    assert result == REVIEWING
    assert context.user_data[ANSWERS_KEY]["name"] == (
        "Test Hotel"
    )
    assert "Данные сохранены" in (
        update.effective_message.replies[-1]
    )


def test_global_guard_rejects_unauthorized_private_user():
    update = make_update(user_id=202)

    with pytest.raises(ApplicationHandlerStop):
        asyncio.run(
            block_disallowed_update(
                update,
                make_context(),
            )
        )

    assert update.effective_message.replies == [
        "Доступ к этому боту закрыт."
    ]


def test_global_guard_rejects_unauthorized_callback():
    update = make_update(
        user_id=202,
        callback_data=CREATE_CONTENT,
    )

    with pytest.raises(ApplicationHandlerStop):
        asyncio.run(
            block_disallowed_update(
                update,
                make_context(),
            )
        )

    assert update.callback_query.answered
    assert update.effective_message.replies == [
        "Доступ к этому боту закрыт."
    ]


def test_application_registers_global_access_guard():
    application = build_application(
        make_settings(),
        generator=SuccessfulGenerator(),
    )

    handler = application.handlers[-1][0]

    assert isinstance(handler, TypeHandler)
    assert handler.callback is block_disallowed_update
