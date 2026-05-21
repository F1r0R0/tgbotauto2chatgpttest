# Telegram автоответчик (Vercel) — расширенная панель

Проект подготовлен для деплоя на **Vercel** через GitHub.

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

## Где лежат ключи
Для быстрого теста ключи уже зашиты в коде:
- `api/config.py`

> Важно: это **небезопасно** для продакшена. После теста сразу замени токены и убери их из репозитория.

## Деплой на Vercel (через GitHub)
1. Запушь проект в GitHub.
2. На Vercel нажми **Add New → Project**.
3. Выбери этот репозиторий.
4. Framework preset: **Other**.
5. Build/Output настройки можно не менять (для Python serverless функции они не нужны).
6. Нажми **Deploy**.

После деплоя твой URL будет вида:
`https://<project-name>.vercel.app`

Webhook endpoint:
`https://<project-name>.vercel.app/api/webhook`

## Автоматическая установка webhook на Vercel
При первом входящем запросе функция сама вызывает `setWebhook` в Telegram.
URL берётся так:
1. `PUBLIC_BASE_URL` (если задан)
2. иначе `VERCEL_URL` (автоматически в Vercel)

То есть после деплоя обычно ничего руками делать не нужно — webhook проставится сам.

## Ручная привязка webhook (если нужно)
Если хочешь проставить webhook сразу вручную, выполни:

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<project-name>.vercel.app/api/webhook"}'
```

Проверка:

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

## Локальный запуск
```bash
pip install -r requirements.txt
uvicorn api.webhook:app --host 0.0.0.0 --port 8000
```

## Примечание по env
В проекте оставлена поддержка env-переменных (они перекрывают значения из `api/config.py`), но для твоего запроса всё уже работает «из коробки» даже без env.
