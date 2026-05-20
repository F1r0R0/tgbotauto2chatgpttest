# Telegram Business автоответчик (Vercel)

Бот отвечает **коротко и по делу**, и сообщает, что Zenter передаст информацию владельцу, а владелец скоро ответит.

## Логика ответа
- Ночью: сообщает, что владелец спит и ответит после сна.
- Утром: сообщает, что владелец может быть занят и ответит в ближайшее время.
- Днем/вечером: сообщает, что владелец может быть занят и ответит в ближайшее время или вечером.
- Если NVIDIA API недоступен: `Zenter сейчас не может вам ответить, но постарается ответить в ближайшее время.`
- Cooldown: повторный автоответ одному и тому же чату — не чаще 1 раза в 30 минут.

## Переменные окружения (Vercel)
- `TELEGRAM_BOT_TOKEN` — обязательно
- `TELEGRAM_WEBHOOK_SECRET` — рекомендуется
- `NVIDIA_API_KEY` — опционально (если задан, бот проверяет доступность NVIDIA; если нет, работает только на локальных шаблонах)
- `TIMEZONE_OFFSET_HOURS` — часовой сдвиг для логики утро/день/ночь (по умолчанию `3`)
- `COOLDOWN_SECONDS` — cooldown в секундах (по умолчанию `1800`)

## Deploy
1. Импортируй проект в Vercel.
2. Добавь env переменные.
3. Настрой webhook:
```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<project>.vercel.app/api/webhook",
    "allowed_updates": ["message", "business_message"],
    "secret_token": "<TELEGRAM_WEBHOOK_SECRET>"
  }'
```
4. В Telegram Business подключи бота и настрой где он отвечает (это делается в Telegram UI).


## Если Vercel ругается на `functions` pattern
Если видишь ошибку:
`The pattern "api/webhook.py" defined in functions doesn't match any Serverless Functions` — используй минимальный `vercel.json` с `rewrites` (как в этом репозитории сейчас), без блока `functions`.

Также при импорте проекта выбери:
- **Framework Preset**: `Other`
- **Root Directory**: корень репозитория

После этого redeploy.
