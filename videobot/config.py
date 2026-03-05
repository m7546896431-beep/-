import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ─── Paths ───────────────────────────────────────────────────────────────────
TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/videobot")
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── Limits ──────────────────────────────────────────────────────────────────
FREE_DAILY_LIMIT: int = 5          # downloads per day for free users
FREE_MAX_QUALITY: str = "720"      # max quality for free users (height px)
PAID_MAX_QUALITY: str = "1080"
MAX_FILE_SIZE_MB: int = 50         # Telegram Bot API limit for sendVideo

# ─── Queue ───────────────────────────────────────────────────────────────────
MAX_QUEUE_SIZE: int = 20
DOWNLOAD_TIMEOUT: int = 300        # seconds

# ─── Supported platforms (regex patterns) ────────────────────────────────────
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
]
