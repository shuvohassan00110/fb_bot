import os

BASE_DIR = "/app/data"
os.makedirs(BASE_DIR, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

API_ALL_ENDPOINT = os.getenv("API_ALL_ENDPOINT", "")

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.isdigit()}

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))

CACHE_DB_PATH = os.path.join(BASE_DIR, "cache.sqlite")
STATS_DB_PATH = os.path.join(BASE_DIR, "stats.sqlite")
LOGS_DB_PATH = os.path.join(BASE_DIR, "logs.sqlite")
