import os
import logging
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", "3"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "1800"))

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

_last_reply_by_chat: dict[int, float] = {}
_cooldown_lock = Lock()


def fallback_text_by_time() -> str:
    now_utc = datetime.now(timezone.utc)
    local_hour = (now_utc.hour + TIMEZONE_OFFSET_HOURS) % 24

    if 0 <= local_hour < 6:
        return "Сейчас Zenter спит. Он передаст вам ответ, когда проснется."
    if 6 <= local_hour < 12:
        return "Zenter сейчас может быть занят. Он получил ваше сообщение и ответит в ближайшее время."
    if 12 <= local_hour < 22:
        return "Zenter сейчас может быть занят. Он получил ваше сообщение и ответит в ближайшее время или вечером."
    return "Сейчас поздно. Zenter получил ваше сообщение и ответит позже."


def nvidia_unavailable_text() -> str:
    return "Zenter сейчас не может вам ответить, но постарается ответить в ближайшее время."


def call_qwen(user_text: str) -> str:
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": "qwen/qwen3.5-397b-a17b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Отвечай строго коротко и по делу на русском."
                    "Сообщай только, что Zenter передаст информацию владельцу и он скоро ответит."
                    "Без лишних деталей."
                ),
            },
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 80,
        "temperature": 0.2,
        "top_p": 0.9,
        "stream": False,
    }

    resp = requests.post(NVIDIA_URL, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def tg_send_message(chat_id: int, text: str, business_connection_id: str | None = None) -> None:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if business_connection_id:
        payload["business_connection_id"] = business_connection_id

    resp = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=20)
    resp.raise_for_status()


def extract_message(update: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if "business_message" in update:
        msg = update["business_message"]
        return msg, msg.get("business_connection_id")
    if "message" in update:
        return update["message"], None
    return None, None


def should_reply(chat_id: int) -> bool:
    now_ts = datetime.now(timezone.utc).timestamp()
    with _cooldown_lock:
        last_ts = _last_reply_by_chat.get(chat_id)
        if last_ts and now_ts - last_ts < COOLDOWN_SECONDS:
            return False
        _last_reply_by_chat[chat_id] = now_ts
        return True


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    if WEBHOOK_SECRET:
        token = request.headers.get("x-telegram-bot-api-secret-token", "")
        if token != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid secret token")

    if not TELEGRAM_TOKEN:
        raise HTTPException(status_code=500, detail="Missing TELEGRAM_BOT_TOKEN")

    update = await request.json()
    message, business_connection_id = extract_message(update)
    if not message:
        return JSONResponse({"ok": True, "skipped": "no_supported_message"})

    chat_id = (message.get("chat") or {}).get("id")
    text = message.get("text")
    if not text or not chat_id:
        return JSONResponse({"ok": True, "skipped": "non_text_or_no_chat"})

    if not should_reply(chat_id):
        return JSONResponse({"ok": True, "skipped": "cooldown_active"})

    reply_text = fallback_text_by_time()

    if NVIDIA_API_KEY:
        try:
            _ = call_qwen(text)
        except Exception:
            reply_text = nvidia_unavailable_text()

    try:
        tg_send_message(chat_id, reply_text, business_connection_id)
    except Exception as exc:
        logging.exception("Telegram send failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    return JSONResponse({"ok": True})
