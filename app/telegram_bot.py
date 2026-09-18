import asyncio
import os

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ApplicationHandlerStop,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from app.content_generator import (
    ContentGenerationError,
    ContentGenerator,
)
from app.gemini_provider import GeminiProvider
from app.hotel_data import HotelData
from app.telegram_config import (
    TelegramConfigError,
    TelegramSettings,
    load_telegram_settings,
)
from app.telegram_fields import (
    HOTEL_FIELDS,
    answers_to_hotel,
    empty_field_value,
    parse_field_value,
    split_telegram_text,
)


COLLECTING, REVIEWING = range(2)

ANSWERS_KEY = "answers"
FIELD_INDEX_KEY = "field_index"

CREATE_CONTENT = "create_content"
RESTART_DIALOG = "restart_dialog"


def is_allowed_user(
    user_id: int | None,
    settings: TelegramSettings,
) -> bool:
    return user_id is not None and settings.is_allowed(user_id)


def is_private_allowed_user(
    user_id: int | None,
    chat_type: str | None,
    settings: TelegramSettings,
) -> bool:
    return (
        chat_type == "private"
        and is_allowed_user(user_id, settings)
    )


def _settings(
    context: CallbackContext,
) -> TelegramSettings:
    return context.application.bot_data["settings"]


def _generator(
    context: CallbackContext,
) -> ContentGenerator:
    return context.application.bot_data["generator"]


def _answers(
    context: CallbackContext,
) -> dict[str, object]:
    return context.user_data.setdefault(ANSWERS_KEY, {})


async def _reply(
    update: Update,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            text,
            reply_markup=reply_markup,
        )


async def _ensure_access(
    update: Update,
    context: CallbackContext,
) -> bool:
    user_id = (
        update.effective_user.id
        if update.effective_user
        else None
    )
    chat_type = (
        update.effective_chat.type
        if update.effective_chat
        else None
    )

    if is_private_allowed_user(
        user_id,
        chat_type,
        _settings(context),
    ):
        return True

    if update.callback_query:
        await update.callback_query.answer(
            "Доступ к этому боту закрыт.",
            show_alert=True,
        )

    await _reply(
        update,
        "Доступ к этому боту закрыт.",
    )

    return False


async def block_disallowed_update(
    update: Update,
    context: CallbackContext,
) -> None:
    if not await _ensure_access(update, context):
        raise ApplicationHandlerStop


async def _ask_current_field(
    update: Update,
    context: CallbackContext,
) -> int:
    field_index = context.user_data[FIELD_INDEX_KEY]
    field = HOTEL_FIELDS[field_index]

    await _reply(update, field.question)

    return COLLECTING


def _start_dialog(
    context: CallbackContext,
) -> None:
    context.user_data.clear()
    context.user_data[ANSWERS_KEY] = {}
    context.user_data[FIELD_INDEX_KEY] = 0


def _fact_count(hotel: HotelData) -> int:
    return sum(
        len(items)
        for items in (
            hotel.representative_facts,
            hotel.observations,
            hotel.strengths,
            hotel.limitations,
            hotel.filmed_shots,
        )
    )


def _summary_text(hotel: HotelData) -> str:
    lines = [
        "Проверьте данные перед генерацией:",
        f"Название: {hotel.name}",
    ]

    location = ", ".join(
        value
        for value in (hotel.city, hotel.district)
        if value
    )
    if location:
        lines.append(f"Локация: {location}")

    if hotel.inspection_date:
        lines.append(
            f"Дата инспекции: {hotel.inspection_date}"
        )

    lines.append(
        f"Содержательных фактов: {_fact_count(hotel)}"
    )

    return "\n".join(lines)


def _review_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Создать контент",
                    callback_data=CREATE_CONTENT,
                )
            ],
            [
                InlineKeyboardButton(
                    "Начать заново",
                    callback_data=RESTART_DIALOG,
                )
            ],
        ]
    )


async def start(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    await _reply(
        update,
        "Здравствуйте! Я помогу подготовить "
        "контент об отеле.\n\n"
        "Отправьте /new, чтобы начать новую инспекцию.",
    )

    return ConversationHandler.END


async def new_inspection(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    _start_dialog(context)

    await _reply(
        update,
        "Начинаем новую инспекцию. "
        "Необязательные поля можно пропускать командой /skip.",
    )

    return await _ask_current_field(update, context)


async def cancel(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    context.user_data.clear()

    await _reply(
        update,
        "Диалог отменён. Данные удалены из памяти.",
    )

    return ConversationHandler.END


async def skip_field(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    field_index = context.user_data[FIELD_INDEX_KEY]
    field = HOTEL_FIELDS[field_index]

    if not field.optional:
        await _reply(
            update,
            "Название отеля обязательно. "
            "Введите его текстом.",
        )
        return COLLECTING

    _answers(context)[field.key] = empty_field_value(field)

    return await _move_to_next_field(update, context)


async def receive_value(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    if not update.effective_message:
        return COLLECTING

    field_index = context.user_data[FIELD_INDEX_KEY]
    field = HOTEL_FIELDS[field_index]
    text = update.effective_message.text or ""

    try:
        value = parse_field_value(field, text)
    except ValueError as exc:
        await _reply(update, str(exc))
        return COLLECTING

    if field.key == "name" and not value:
        await _reply(
            update,
            "Название отеля обязательно. "
            "Введите его текстом.",
        )
        return COLLECTING

    _answers(context)[field.key] = value

    return await _move_to_next_field(update, context)


async def _move_to_next_field(
    update: Update,
    context: CallbackContext,
) -> int:
    next_index = context.user_data[FIELD_INDEX_KEY] + 1

    if next_index < len(HOTEL_FIELDS):
        context.user_data[FIELD_INDEX_KEY] = next_index
        return await _ask_current_field(update, context)

    hotel = answers_to_hotel(_answers(context))
    errors = hotel.validate()

    if errors:
        context.user_data[FIELD_INDEX_KEY] = next(
            index
            for index, field in enumerate(HOTEL_FIELDS)
            if field.key == "representative_facts"
        )

        await _reply(update, errors[0])

        return await _ask_current_field(update, context)

    await _reply(
        update,
        _summary_text(hotel),
        reply_markup=_review_buttons(),
    )

    return REVIEWING


async def review_callback(
    update: Update,
    context: CallbackContext,
) -> int:
    if not await _ensure_access(update, context):
        return ConversationHandler.END

    query = update.callback_query
    if not query:
        return REVIEWING

    await query.answer()

    if query.data == RESTART_DIALOG:
        _start_dialog(context)

        await _reply(
            update,
            "Начинаем заново.",
        )

        return await _ask_current_field(update, context)

    if query.data != CREATE_CONTENT:
        return REVIEWING

    hotel = answers_to_hotel(_answers(context))

    await _reply(
        update,
        "Создаю пять разделов. Это может занять немного времени.",
    )

    try:
        content = await asyncio.to_thread(
            _generator(context).generate,
            hotel,
        )
    except ContentGenerationError as exc:
        await _reply(
            update,
            f"Ошибка: {exc}\n"
            "Данные сохранены. Попробуйте ещё раз.",
        )
        return REVIEWING

    for title, body in content.as_sections().items():
        section = f"## {title}\n\n{body}"

        for chunk in split_telegram_text(section):
            await _reply(update, chunk)

    await _reply(
        update,
        "Проверьте все факты вручную перед публикацией.",
    )

    context.user_data.clear()

    return ConversationHandler.END


def build_application(
    settings: TelegramSettings,
    generator: ContentGenerator | None = None,
) -> Application:
    if generator is None:
        provider = GeminiProvider(
            settings.gemini_api_key,
            settings.gemini_model,
        )
        generator = ContentGenerator(provider)

    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .concurrent_updates(False)
        .build()
    )

    application.bot_data["settings"] = settings
    application.bot_data["generator"] = generator

    application.add_handler(
        TypeHandler(Update, block_disallowed_update),
        group=-1,
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("new", new_inspection)
        ],
        states={
            COLLECTING: [
                CommandHandler("skip", skip_field),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_value,
                ),
            ],
            REVIEWING: [
                CallbackQueryHandler(review_callback),
            ],
        },
        fallbacks=[
            CommandHandler("new", new_inspection),
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
    )

    application.add_handler(conversation)

    return application


def main() -> None:
    load_dotenv()

    try:
        settings = load_telegram_settings(os.environ)
    except TelegramConfigError as exc:
        print(f"Ошибка: {exc}")
        raise SystemExit(1) from exc

    application = build_application(settings)
    application.run_polling()


if __name__ == "__main__":
    main()
