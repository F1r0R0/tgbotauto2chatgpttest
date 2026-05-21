import json
import logging
import os
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
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))
RUNTIME_OWNER_CHAT_ID = OWNER_CHAT_ID
TIMEZONE_OFFSET_HOURS = int(os.getenv("TIMEZONE_OFFSET_HOURS", "3"))
FORWARD_TO_OWNER = os.getenv("FORWARD_TO_OWNER", "1") == "1"

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

_lock = Lock()
_last_reply_by_chat: dict[int, float] = {}
_chat_stats: dict[int, int] = {}
_owner_state: dict[int, str] = {}

settings: dict[str, Any] = {
    "enabled": True,
    "quiet_hours_enabled": True,
    "quiet_start": 0,
    "quiet_end": 6,
    "cooldown_seconds": 1800,
    "use_nvidia_check": True,
    "forward_to_owner": FORWARD_TO_OWNER,
    "allowlist_mode": False,
    "allowed_chats": [],
    "night_text": "Сейчас Zenter спит. Он передаст вам ответ, когда проснется.",
    "morning_text": "Zenter сейчас может быть занят. Он получил ваше сообщение и ответит в ближайшее время.",
    "day_text": "Zenter сейчас может быть занят. Он получил ваше сообщение и ответит в ближайшее время или вечером.",
    "evening_text": "Сейчас поздно. Zenter получил ваше сообщение и ответит позже.",
    "nvidia_fail_text": "Zenter сейчас не может вам ответить, но постарается ответить в ближайшее время.",
    "blocked_words": [],
}




def is_start_trigger(text: str) -> bool:
    t = (text or '').strip().lower()
    if t in {'start', 'старт'}:
        return True
    if not t.startswith('/start'):
        return False

    # Supports: /start, /start payload, /start@BotName, /start@BotName payload
    head = t.split(maxsplit=1)[0]
    return head == '/start' or head.startswith('/start@')

def tg_api(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    r = requests.post(f"{TG_API}/{method}", json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def owner_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [
            ["📊 Статус", "🔁 Автоответ ON/OFF"],
            ["⏱ +5 мин", "⏱ -5 мин"],
            ["🌙 Quiet ON/OFF", "🤖 NVIDIA ON/OFF"],
            ["👤 Forward owner ON/OFF", "🧭 Allowlist ON/OFF"],
            ["➕ Add allowed chat", "➖ Remove allowed chat"],
            ["🚫 Add blocked word", "✅ Remove blocked word"],
            ["📝 Текст: Ночь", "📝 Текст: Утро"],
            ["📝 Текст: День", "📝 Текст: Вечер"],
            ["🧯 Текст: NVIDIA fallback", "📦 Export settings"],
            ["📥 Import settings", "🔙 Сброс состояния"],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def current_local_hour() -> int:
    return (datetime.now(timezone.utc).hour + TIMEZONE_OFFSET_HOURS) % 24


def get_time_text() -> str:
    h = current_local_hour()
    if 0 <= h < 6:
        return settings["night_text"]
    if 6 <= h < 12:
        return settings["morning_text"]
    if 12 <= h < 22:
        return settings["day_text"]
    return settings["evening_text"]


def is_quiet_hours() -> bool:
    if not settings["quiet_hours_enabled"]:
        return False
    h = current_local_hour()
    start, end = settings["quiet_start"], settings["quiet_end"]
    if start < end:
        return start <= h < end
    return h >= start or h < end


def should_reply(chat_id: int) -> bool:
    now_ts = datetime.now(timezone.utc).timestamp()
    cooldown = max(0, int(settings["cooldown_seconds"]))
    with _lock:
        last = _last_reply_by_chat.get(chat_id)
        if last and now_ts - last < cooldown:
            return False
        _last_reply_by_chat[chat_id] = now_ts
        _chat_stats[chat_id] = _chat_stats.get(chat_id, 0) + 1
        return True


def extract_message(update: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if "business_message" in update:
        msg = update["business_message"]
        return msg, msg.get("business_connection_id")
    if "message" in update:
        return update["message"], None
    return None, None


def nvidia_check(text: str) -> None:
    headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "model": "qwen/qwen3.5-397b-a17b",
        "messages": [{"role": "system", "content": "Коротко."}, {"role": "user", "content": text}],
        "max_tokens": 32,
        "temperature": 0.1,
        "stream": False,
    }
    r = requests.post(NVIDIA_URL, headers=headers, json=payload, timeout=12)
    r.raise_for_status()


def get_owner_chat_id() -> int:
    return RUNTIME_OWNER_CHAT_ID


def owner_status_text() -> str:
    return (
        "⚙️ Панель\n"
        f"Автоответ: {'ON' if settings['enabled'] else 'OFF'}\n"
        f"Quiet: {'ON' if settings['quiet_hours_enabled'] else 'OFF'} ({settings['quiet_start']}-{settings['quiet_end']})\n"
        f"Cooldown: {settings['cooldown_seconds']} сек\n"
        f"NVIDIA: {'ON' if settings['use_nvidia_check'] else 'OFF'}\n"
        f"Forward owner: {'ON' if settings['forward_to_owner'] else 'OFF'}\n"
        f"Allowlist: {'ON' if settings['allowlist_mode'] else 'OFF'} ({len(settings['allowed_chats'])} chats)\n"
        f"Blocked words: {len(settings['blocked_words'])}\n"
        f"Чатов с ответами: {len(_chat_stats)} | Всего автоответов: {sum(_chat_stats.values())}"
    )


def handle_owner_button(chat_id: int, text: str) -> str:
    pending = _owner_state.get(chat_id, "")

    if text == "🔙 Сброс состояния":
        _owner_state.pop(chat_id, None)
        return "Состояние ввода сброшено."

    if pending.startswith("settext:"):
        key = pending.split(":", 1)[1]
        settings[key] = text
        _owner_state.pop(chat_id, None)
        return f"✅ Текст обновлен: {key}"

    if pending == "add_blocked":
        word = text.lower().strip()
        if word and word not in settings["blocked_words"]:
            settings["blocked_words"].append(word)
        _owner_state.pop(chat_id, None)
        return f"✅ Добавлено blocked word: {word}"

    if pending == "remove_blocked":
        word = text.lower().strip()
        settings["blocked_words"] = [w for w in settings["blocked_words"] if w != word]
        _owner_state.pop(chat_id, None)
        return f"✅ Удалено blocked word: {word}"

    if pending == "add_allowed_chat":
        try:
            cid = int(text.strip())
            if cid not in settings["allowed_chats"]:
                settings["allowed_chats"].append(cid)
            _owner_state.pop(chat_id, None)
            return f"✅ allowed chat added: {cid}"
        except ValueError:
            return "Отправь числовой chat_id"

    if pending == "remove_allowed_chat":
        try:
            cid = int(text.strip())
            settings["allowed_chats"] = [x for x in settings["allowed_chats"] if x != cid]
            _owner_state.pop(chat_id, None)
            return f"✅ allowed chat removed: {cid}"
        except ValueError:
            return "Отправь числовой chat_id"

    if pending == "import_settings":
        try:
            incoming = json.loads(text)
            if isinstance(incoming, dict):
                for k in settings.keys():
                    if k in incoming:
                        settings[k] = incoming[k]
                _owner_state.pop(chat_id, None)
                return "✅ Настройки импортированы"
            return "Ожидался JSON-объект"
        except json.JSONDecodeError:
            return "Невалидный JSON"

    mapping = {
        "📊 Статус": "status",
        "🔁 Автоответ ON/OFF": "toggle_enabled",
        "⏱ +5 мин": "cd_plus",
        "⏱ -5 мин": "cd_minus",
        "🌙 Quiet ON/OFF": "toggle_quiet",
        "🤖 NVIDIA ON/OFF": "toggle_nvidia",
        "👤 Forward owner ON/OFF": "toggle_forward",
        "🧭 Allowlist ON/OFF": "toggle_allowlist",
        "➕ Add allowed chat": "add_allowed_chat",
        "➖ Remove allowed chat": "remove_allowed_chat",
        "🚫 Add blocked word": "add_blocked",
        "✅ Remove blocked word": "remove_blocked",
        "📝 Текст: Ночь": "night_text",
        "📝 Текст: Утро": "morning_text",
        "📝 Текст: День": "day_text",
        "📝 Текст: Вечер": "evening_text",
        "🧯 Текст: NVIDIA fallback": "nvidia_fail_text",
        "📦 Export settings": "export",
        "📥 Import settings": "import",
    }

    action = mapping.get(text)
    if action == "status":
        return owner_status_text()
    if action == "toggle_enabled":
        settings["enabled"] = not settings["enabled"]
        return f"✅ Автоответ: {'ON' if settings['enabled'] else 'OFF'}"
    if action == "cd_plus":
        settings["cooldown_seconds"] = int(settings["cooldown_seconds"]) + 300
        return f"✅ Cooldown: {settings['cooldown_seconds']} сек"
    if action == "cd_minus":
        settings["cooldown_seconds"] = max(0, int(settings["cooldown_seconds"]) - 300)
        return f"✅ Cooldown: {settings['cooldown_seconds']} сек"
    if action == "toggle_quiet":
        settings["quiet_hours_enabled"] = not settings["quiet_hours_enabled"]
        return f"✅ Quiet: {'ON' if settings['quiet_hours_enabled'] else 'OFF'}"
    if action == "toggle_nvidia":
        settings["use_nvidia_check"] = not settings["use_nvidia_check"]
        return f"✅ NVIDIA: {'ON' if settings['use_nvidia_check'] else 'OFF'}"
    if action == "toggle_forward":
        settings["forward_to_owner"] = not settings["forward_to_owner"]
        return f"✅ Forward owner: {'ON' if settings['forward_to_owner'] else 'OFF'}"
    if action == "toggle_allowlist":
        settings["allowlist_mode"] = not settings["allowlist_mode"]
        return f"✅ Allowlist: {'ON' if settings['allowlist_mode'] else 'OFF'}"
    if action in {"add_allowed_chat", "remove_allowed_chat", "add_blocked", "remove_blocked"}:
        _owner_state[chat_id] = action
        return "Отправь значение следующим сообщением"
    if action in {"night_text", "morning_text", "day_text", "evening_text", "nvidia_fail_text"}:
        _owner_state[chat_id] = f"settext:{action}"
        return f"Отправь новый текст для {action}"
    if action == "export":
        return json.dumps(settings, ensure_ascii=False)
    if action == "import":
        _owner_state[chat_id] = "import_settings"
        return "Отправь JSON настроек одним сообщением"

    if is_start_trigger(text):
        return "Панель управления активирована. Нажимай кнопки ниже."
    return "Нажми кнопку на панели ниже."


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
    text = (message.get("text") or "").strip()
    if not text or not chat_id:
        return JSONResponse({"ok": True, "skipped": "non_text_or_no_chat"})

    global RUNTIME_OWNER_CHAT_ID

    # bootstrap owner panel on /start if OWNER_CHAT_ID is not configured
    if is_start_trigger(text) and RUNTIME_OWNER_CHAT_ID == 0:
        RUNTIME_OWNER_CHAT_ID = chat_id
        tg_api("sendMessage", {
            "chat_id": chat_id,
            "text": "✅ Панель активирована для этого чата. Если нужно закрепить навсегда — укажи OWNER_CHAT_ID в env.",
            "reply_markup": owner_keyboard(),
        })
        return JSONResponse({"ok": True, "owner_bootstrap": True})

    if get_owner_chat_id() and chat_id == get_owner_chat_id():
        resp = handle_owner_button(chat_id, text)
        tg_api("sendMessage", {"chat_id": chat_id, "text": resp, "reply_markup": owner_keyboard()})
        return JSONResponse({"ok": True, "owner_panel": True})

    if is_start_trigger(text):
        tg_api("sendMessage", {
            "chat_id": chat_id,
            "text": "✅ Бот на связи. Напишите сообщение — я отвечу автоматически по текущим настройкам.",
        })
        return JSONResponse({"ok": True, "start_ack": True})

    if settings["allowlist_mode"] and chat_id not in settings["allowed_chats"]:
        return JSONResponse({"ok": True, "skipped": "not_in_allowlist"})
    if not settings["enabled"]:
        return JSONResponse({"ok": True, "skipped": "disabled"})
    if any(w in text.lower() for w in settings["blocked_words"]):
        return JSONResponse({"ok": True, "skipped": "blocked_word"})
    if not should_reply(chat_id):
        return JSONResponse({"ok": True, "skipped": "cooldown_active"})

    reply_text = settings["night_text"] if is_quiet_hours() else get_time_text()
    if settings["use_nvidia_check"] and NVIDIA_API_KEY:
        try:
            nvidia_check(text)
        except Exception:
            reply_text = settings["nvidia_fail_text"]

    owner_chat_id = get_owner_chat_id()
    if settings["forward_to_owner"] and owner_chat_id:
        preview = text[:800]
        tg_api("sendMessage", {"chat_id": owner_chat_id, "text": f"📩 Новое сообщение от chat_id={chat_id}:\n{preview}"})

    payload = {"chat_id": chat_id, "text": reply_text}
    if business_connection_id:
        payload["business_connection_id"] = business_connection_id
    tg_api("sendMessage", payload)

    return JSONResponse({"ok": True})
