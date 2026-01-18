import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ALL_ENDPOINT = os.getenv("API_ALL_ENDPOINT", "")  # e.g. https://your-api/api/all

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # e.g. @gadgetpremiumzone
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "")  # e.g. https://t.me/gadgetpremiumzone

ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}

ZIP_PART_MAX_MB = int(os.getenv("ZIP_PART_MAX_MB", "45"))  # telegram safe-ish
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "900"))

# Default toggles (admin can change at runtime)
DEFAULT_FORCE_JOIN = os.getenv("DEFAULT_FORCE_JOIN", "1") == "1"
DEFAULT_MAINTENANCE = os.getenv("DEFAULT_MAINTENANCE", "0") == "1"
