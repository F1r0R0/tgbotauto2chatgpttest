# Telegram автоответчик (VPS) — расширенная панель

Проект переведён с Netlify на обычный VPS-запуск через FastAPI/Uvicorn.

## Что умеет бот
- Переключатель автоответа
- Cooldown +/- 5 минут
- Quiet hours ON/OFF
- NVIDIA check ON/OFF
- Forward входящих владельцу (`OWNER_CHAT_ID`)
- Allowlist mode (отвечать только выбранным chat_id)
- Добавление/удаление blocked words
- Редактирование текстов ответа по времени
- Export/Import настроек JSON
- Статус и статистика

## Env
- `TELEGRAM_BOT_TOKEN` (обязательно)
- `OWNER_CHAT_ID` (опционально, если не задан — первый `/start` назначит owner до рестарта)
- `TELEGRAM_WEBHOOK_SECRET` (рекомендуется)
- `NVIDIA_API_KEY` (опционально)
- `TIMEZONE_OFFSET_HOURS` (default 3)
- `FORWARD_TO_OWNER` (`1`/`0`, default `1`)

## Запуск на VPS
1. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запусти API:
   ```bash
   uvicorn api.webhook:app --host 0.0.0.0 --port 8000
   ```
3. Настрой reverse proxy (Nginx/Caddy) на `http://127.0.0.1:8000`.
4. Установи webhook Telegram на публичный URL:
   `https://<your-domain>/api/webhook`

## Проверка
- `GET /` → `{"status":"ok"}`
- `POST /api/webhook` принимает апдейты Telegram.
