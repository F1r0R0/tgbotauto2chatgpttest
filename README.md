# Telegram Business автоответчик (Vercel) — расширенная панель

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
- `OWNER_CHAT_ID` (обязательно)
- `TELEGRAM_WEBHOOK_SECRET` (рекомендуется)
- `NVIDIA_API_KEY` (опционально)
- `TIMEZONE_OFFSET_HOURS` (default 3)
- `FORWARD_TO_OWNER` (`1`/`0`, default `1`)

## Deploy
1. Preset: **Other**
2. Добавь env
3. setWebhook на `/api/webhook`


## Если /start ничего не делает

- Триггер панели понимает не только `/start`, но и `start`/`старт` (и `/start payload`).
- Проверь, что webhook установлен на `/api/webhook`.
- Если `OWNER_CHAT_ID` не задан, бот теперь автоматически назначает владельцем **первый чат, где пришел `/start`** (после рестарта это надо повторить).
- Чтобы закрепить владельца навсегда, явно задай `OWNER_CHAT_ID` в env.
