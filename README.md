# Telegram автоответчик (Netlify) — расширенная панель

Теперь всё управление через кнопки + добавлены новые фишки.

## Новые функции
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

## Обычный бот vs Telegram Business
Бот работает **как обычный бот** (без Telegram Business): панель, `/start`, автоответы по обычным сообщениям (`message`) доступны.

Telegram Business нужен только для сценария, когда сообщения приходят как `business_message` и бот отвечает в business-контексте.

## Панель владельца
Работает только для `OWNER_CHAT_ID`.
Кнопки:
- `📊 Статус`
- `🔁 Автоответ ON/OFF`
- `⏱ +5 мин`, `⏱ -5 мин`
- `🌙 Quiet ON/OFF`, `🤖 NVIDIA ON/OFF`
- `👤 Forward owner ON/OFF`, `🧭 Allowlist ON/OFF`
- `➕ Add allowed chat`, `➖ Remove allowed chat`
- `🚫 Add blocked word`, `✅ Remove blocked word`
- `📝 Текст: Ночь/Утро/День/Вечер`
- `🧯 Текст: NVIDIA fallback`
- `📦 Export settings`, `📥 Import settings`

## Env
- `TELEGRAM_BOT_TOKEN` (обязательно)
- `OWNER_CHAT_ID` (опционально, если не задан — первый `/start` назначит owner до рестарта)
- `TELEGRAM_WEBHOOK_SECRET` (рекомендуется)
- `NVIDIA_API_KEY` (опционально)
- `TIMEZONE_OFFSET_HOURS` (default 3)
- `FORWARD_TO_OWNER` (`1`/`0`, default `1`)

## Deploy (Netlify)
1. Подключи репозиторий в Netlify.
2. Добавь все env-переменные из раздела `Env`.
3. Deploy site (Python Functions включатся автоматически через `netlify/functions`).
4. Установи webhook Telegram на URL: `https://<your-site>.netlify.app/api/webhook`.


## Если /start ничего не делает

- Триггер панели понимает не только `/start`, но и `start`/`старт` (и `/start payload`).
- Проверь, что webhook установлен на `/api/webhook` (Netlify перенаправит на функцию).
- Если `OWNER_CHAT_ID` не задан, бот теперь автоматически назначает владельцем **первый чат, где пришел `/start`** (после рестарта это надо повторить).
- Чтобы закрепить владельца навсегда, явно задай `OWNER_CHAT_ID` в env.
