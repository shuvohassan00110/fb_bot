import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
API_ALL_ENDPOINT = os.getenv("API_ALL_ENDPOINT", "http://127.0.0.1:5000/api/all")

# Force join
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@YourChannelUsername")  # e.g. @gadgetpremiumzone
CHANNEL_JOIN_URL = os.getenv("CHANNEL_JOIN_URL", "https://t.me/YourChannelUsername")

# Admin panel
ADMIN_IDS = set(int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip().isdigit())

# Cache
CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "cache.sqlite")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))  # 10 minutes

# Stats DB
STATS_DB_PATH = os.getenv("STATS_DB_PATH", "stats.sqlite")

# Network
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))

# ZIP (size-safe splitting)
MAX_IMAGE_DOWNLOAD_MB = int(os.getenv("MAX_IMAGE_DOWNLOAD_MB", "6"))  # skip huge single images
ZIP_PART_MAX_MB = int(os.getenv("ZIP_PART_MAX_MB", "45"))             # keep under Telegram limits
MAX_ZIP_IMAGES_TOTAL = int(os.getenv("MAX_ZIP_IMAGES_TOTAL", "120"))  # total try limit (unlimited feel)

DEVELOPER_TAG = "@mrseller_00"
