# Hotel Expert AI

Учебное Python-приложение для подготовки экспертного русскоязычного контента по проверенным данным гостиничных инспекций.

## Статус

Разрабатывается локальная первая версия. Любой созданный AI-текст необходимо проверить перед публикацией.

## Локальная установка

1. Создайте окружение: `python3 -m venv .venv`.
2. Активируйте его: `source .venv/bin/activate`.
3. Установите зависимости: `python -m pip install -r requirements.txt`.
4. Скопируйте `.env.example` в `.env` и заполните все локальные переменные:

   ```text
   GEMINI_API_KEY=
   GEMINI_MODEL=gemini-3.5-flash-lite
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_ALLOWED_USER_IDS=
