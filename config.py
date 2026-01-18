import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
API_ALL_ENDPOINT = os.getenv("API_ALL_ENDPOINT", "http://127.0.0.1:5000/api/all")

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@gadgetpremiumzone")
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "https://t.me/gadgetpremiumzone")

ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "7857957075").split(",") if x.strip().isdigit())

CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "cache.sqlite")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))

STATS_DB_PATH = os.getenv("STATS_DB_PATH", "stats.sqlite")
ADMIN_FLAGS_DB = os.getenv("ADMIN_FLAGS_DB", "admin_flags.sqlite")
LOGS_DB_PATH = os.getenv("LOGS_DB_PATH", "logs.sqlite")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))

MAX_IMAGE_DOWNLOAD_MB = int(os.getenv("MAX_IMAGE_DOWNLOAD_MB", "6"))
ZIP_PART_MAX_MB = int(os.getenv("ZIP_PART_MAX_MB", "45"))
MAX_ZIP_IMAGES_TOTAL = int(os.getenv("MAX_ZIP_IMAGES_TOTAL", "120"))

DEVELOPER_TAG = "@mrseller_00"
