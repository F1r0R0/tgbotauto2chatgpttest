"""Project configuration.
Temporary hardcoded credentials for quick Vercel test deploy.
"""

TELEGRAM_BOT_TOKEN = "8901247022:AAGXJIqibhRydmSVrpW8JvJk5QWykpeOXrM"
NVIDIA_API_KEY = "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"
NVIDIA_MODEL = "qwen/qwen3.5-397b-a17b"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Optional values still may be overridden by env in Vercel project settings.
DEFAULT_WEBHOOK_SECRET = ""
DEFAULT_OWNER_CHAT_ID = 0
DEFAULT_TIMEZONE_OFFSET_HOURS = 3
DEFAULT_FORWARD_TO_OWNER = True
