# Telegram Bot Implementation Plan

> **For implementation:** Complete the tasks in order. Keep the bot local, private, and free of secrets in Git.

**Goal:** Add a private Telegram interface that collects hotel-inspection data step by step and uses the existing AI core to send five content sections after the user confirms.

**Architecture:** `telegram_config` loads and validates local settings. `telegram_fields` converts Telegram text into the existing `HotelData` model and splits outbound messages. `telegram_bot` owns only Telegram commands, conversation state, access control, buttons, and delivery; it reuses `GeminiProvider`, `ContentGenerator`, and `GeneratedContent`.

**Tech Stack:** Python 3.13, `python-telegram-bot` v21–22, `python-dotenv`, pytest, existing Gemini client.

**Spec:** `docs/superpowers/specs/2026-09-17-telegram-bot-design.md`

## Global constraints

- Never write, print, commit, or place a real Telegram or Gemini token in tests, docs, or source code.
- Load secrets from the local `.env`; keep `.env` ignored.
- Restrict every command, message, and button callback to `TELEGRAM_ALLOWED_USER_IDS`.
- Use `ConversationHandler` with sequential update handling (`concurrent_updates(False)`).
- Keep the initial version in-memory, local polling only, and single-user in practice.
- Keep Gemini calls out of the event loop with `asyncio.to_thread`.
- Run focused tests before each commit and the full suite before the final commit.

---

## Task 1: Add Telegram dependency and typed configuration

**Files:**
- Modify: `requirements.txt`
- Create: `app/telegram_config.py`
- Create: `tests/test_telegram_config.py`

- [ ] **Step 1: Write failing configuration tests.**

  Cover a valid mapping with a token, Gemini key/model, and comma-separated numeric IDs; whitespace around IDs; missing bot token; absent/blank allowed-ID value; and malformed values such as `123,abc`. Assert Russian error messages and `is_allowed()` behavior.

- [ ] **Step 2: Run the focused test to prove it fails.**

  Run: `python -m pytest tests/test_telegram_config.py -v`

- [ ] **Step 3: Add the runtime dependency.**

  Add exactly `python-telegram-bot>=21,<23` to `requirements.txt`, then install project requirements in the active virtual environment:

  Run: `python -m pip install -r requirements.txt`

- [ ] **Step 4: Implement `app/telegram_config.py`.**

  Create a frozen `TelegramSettings` dataclass with `bot_token`, `allowed_user_ids`, `gemini_api_key`, and `gemini_model`, plus `is_allowed(user_id: int) -> bool`.

  Implement `load_telegram_settings(env: Mapping[str, str]) -> TelegramSettings`. Parse the allowed IDs by comma, trim whitespace, reject empty segments and non-integers, and reject an empty resulting set. Raise `TelegramConfigError` with these exact Russian messages:

  - `Не задан TELEGRAM_BOT_TOKEN в локальном файле .env.`
  - `Не задан TELEGRAM_ALLOWED_USER_IDS в локальном файле .env.`
  - `TELEGRAM_ALLOWED_USER_IDS должен содержать числа через запятую.`

  Require `GEMINI_API_KEY` and `GEMINI_MODEL` too, with similarly specific local-`.env` errors, so polling never starts with incomplete AI configuration.

- [ ] **Step 5: Run focused tests.**

  Run: `python -m pytest tests/test_telegram_config.py -v`

- [ ] **Step 6: Commit the isolated change.**

  Run: `git add requirements.txt app/telegram_config.py tests/test_telegram_config.py && git diff --cached --check && git commit -m "feat: add Telegram bot configuration"`

## Task 2: Convert text answers to hotel data and split messages safely

**Files:**
- Create: `app/telegram_fields.py`
- Create: `tests/test_telegram_fields.py`

- [ ] **Step 1: Write failing field-helper tests.**

  Test that multiline list input ignores blank lines and trims entries; optional skipped values become empty strings or lists; room counts accept a positive integer and reject `0`, negative values, and non-numeric text; `HotelData.from_dict()` receives the expected fields; and an over-4096-character outbound text is split into chunks no longer than 4096 while preserving all text.

- [ ] **Step 2: Run the focused test to prove it fails.**

  Run: `python -m pytest tests/test_telegram_fields.py -v`

- [ ] **Step 3: Implement `app/telegram_fields.py`.**

  Define the ordered 14-field metadata once: key, Russian question, value kind (`text`, `list`, or `room_count`), and whether `/skip` is accepted. Keep the fields in the exact `HotelData` order from the approved spec.

  Implement helpers:

  - `parse_list_text(text) -> list[str]` for non-empty trimmed lines;
  - `parse_room_count(text) -> int` with a Russian `ValueError` stating that the number of rooms must be a positive integer;
  - `answers_to_hotel(answers) -> HotelData`, using `HotelData.from_dict()` rather than reproducing data-cleaning rules;
  - `split_telegram_text(text, limit=4096) -> list[str]`, preferring newline breaks and splitting an individual long line only when unavoidable.

- [ ] **Step 4: Run focused tests.**

  Run: `python -m pytest tests/test_telegram_fields.py -v`

- [ ] **Step 5: Commit the isolated change.**

  Run: `git add app/telegram_fields.py tests/test_telegram_fields.py && git diff --cached --check && git commit -m "feat: prepare Telegram hotel input fields"`

## Task 3: Build private step-by-step Telegram conversation

**Files:**
- Create: `app/telegram_bot.py`
- Create: `tests/test_telegram_bot.py`

- [ ] **Step 1: Write failing bot-flow tests without network access.**

  Use small fake update/message/callback objects and `asyncio.run()` (not an extra async-test dependency). Verify unauthorized users receive the closed-access message and never create answers; `/new` clears old answers and asks for the hotel name; `/skip` stores the correct empty value for optional fields but rejects it for the name; invalid room count repeats the same question; `/cancel` clears state; and the final validation returns the user to `representative_facts` when all meaningful fact fields are empty.

- [ ] **Step 2: Run the focused test to prove it fails.**

  Run: `python -m pytest tests/test_telegram_bot.py -v`

- [ ] **Step 3: Implement conversation and access control.**

  Implement `/start`, `/new`, `/skip`, and `/cancel` as async handlers. Store only `answers` and current field index in `context.user_data`. Check allowed IDs before every command, text update, and callback query; reply `Доступ к этому боту закрыт.` to unauthorized users.

  At the final answer, call `answers_to_hotel()` and the existing `HotelData.validate()`. If `name` is missing, repeat its question. If validation says no meaningful fact exists, explain the requirement and set the index back to `representative_facts`. Do not clear valid answers at this point.

  Render a concise Russian summary (name, non-empty location/date, and fact count) followed by inline buttons `Создать контент` and `Начать заново`.

- [ ] **Step 4: Implement application startup.**

  Implement `build_application(settings, generator=None)` with `ApplicationBuilder`, `.concurrent_updates(False)`, and a `ConversationHandler`; accept an injected generator for tests. Implement `main()` to call `load_dotenv()`, load settings from `os.environ`, instantiate `GeminiProvider(settings.gemini_api_key, settings.gemini_model)` and `ContentGenerator`, then call `run_polling()`.

  Add an executable module entry point so the documented launch command is `python -m app.telegram_bot`. Catch `TelegramConfigError` at startup, print only its safe Russian message, and exit nonzero.

- [ ] **Step 5: Run focused tests.**

  Run: `python -m pytest tests/test_telegram_bot.py -v`

## Task 4: Generate and deliver the five sections

**Files:**
- Modify: `app/telegram_bot.py`
- Modify: `tests/test_telegram_bot.py`

- [ ] **Step 1: Add failing generation-delivery tests.**

  Inject a fake `ContentGenerator` returning a real `GeneratedContent` with five short values. Assert the confirmation callback sends exactly five titled sections in `GeneratedContent.as_sections()` order plus the manual fact-check reminder, then clears the dialog. Add a long-section fixture and assert every sent Telegram message is at most 4096 characters. Add a generator that raises `ContentGenerationError`; assert its Russian message is shown and saved answers/review state remain for another confirmation attempt.

- [ ] **Step 2: Run the focused test to prove it fails.**

  Run: `python -m pytest tests/test_telegram_bot.py -v`

- [ ] **Step 3: Implement generation callback.**

  On `Создать контент`, acknowledge the callback, create `HotelData` from saved answers, send a short progress message, and call `await asyncio.to_thread(generator.generate, hotel)`. For each `(title, body)` from `GeneratedContent.as_sections()`, send `## {title}` and the body, using `split_telegram_text()` for every outbound message. Then send `Проверьте все факты вручную перед публикацией.`

  On `ContentGenerationError`, show its existing Russian message followed by `Данные сохранены. Попробуйте ещё раз.` and keep the user in the review state. On success, clear only this user’s dialog data and finish the conversation. On `Начать заново`, clear answers and return to the name question.

- [ ] **Step 4: Run all bot-focused tests.**

  Run: `python -m pytest tests/test_telegram_config.py tests/test_telegram_fields.py tests/test_telegram_bot.py -v`

- [ ] **Step 5: Commit the bot implementation.**

  Run: `git add app/telegram_bot.py tests/test_telegram_bot.py && git diff --cached --check && git commit -m "feat: add private Telegram hotel assistant"`

## Task 5: Document launch and verify the full project

**Files:**
- Modify: `README.md`
- Modify: `.env.example` only if its Telegram variable descriptions need correction

- [ ] **Step 1: Add concise README instructions.**

  Document: populate local `.env` with `GEMINI_API_KEY`, `GEMINI_MODEL`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_ALLOWED_USER_IDS`; launch with `python -m app.telegram_bot`; stop with `Ctrl+C`; the `/start`, `/new`, `/skip`, and `/cancel` commands; and how to add another person by appending their numeric ID to the comma-separated allowed-ID list then restarting. State that their requests consume the owner’s configured Gemini quota.

- [ ] **Step 2: Run static and automated checks.**

  Run: `python -m py_compile app/telegram_config.py app/telegram_fields.py app/telegram_bot.py`

  Run: `python -m pytest -v`

- [ ] **Step 3: Perform manual local acceptance.**

  Run `python -m app.telegram_bot`, message the bot `/new`, enter an example hotel, use `/skip` for one optional field, confirm the summary, and verify five titled sections arrive. Stop polling with `Ctrl+C`. Test `/cancel` in a fresh dialog. Do not paste any token into the terminal transcript or Git.

- [ ] **Step 4: Commit documentation and publish branch.**

  Run: `git add README.md .env.example && git diff --cached --check && git commit -m "docs: explain Telegram bot launch"`

  Run: `git status --short && git push -u origin feat/telegram-bot`

  Expected final status: no uncommitted changes and remote branch `origin/feat/telegram-bot` exists.
