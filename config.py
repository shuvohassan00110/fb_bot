import os

# ===============================
# Writable directory (Choreo)
# ===============================
BASE_DIR = "/tmp/botdata"
os.makedirs(BASE_DIR, exist_ok=True)

# ===============================
# Core bot settings
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ALL_ENDPOINT = os.getenv("API_ALL_ENDPOINT", "")

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "")

ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

# ===============================
# Timeouts & limits  ✅ (FIX)
# ===============================
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))

# 🔥 THIS WAS MISSING
MAX_IMAGE_DOWNLOAD_MB = int(os.getenv("MAX_IMAGE_DOWNLOAD_MB", "6"))

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))

# ===============================
# SQLite paths (writable)
# ===============================
CACHE_DB_PATH = os.path.join(BASE_DIR, "cache.sqlite")
STATS_DB_PATH = os.path.join(BASE_DIR, "stats.sqlite")
LOGS_DB_PATH = os.path.join(BASE_DIR, "logs.sqlite")
