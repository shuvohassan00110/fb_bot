import re
import time
import threading
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InlineQueryResultArticle, InputTextMessageContent
)

from config import (
    BOT_TOKEN, API_ALL_ENDPOINT,
    REQUIRED_CHANNEL, CHANNEL_JOIN_URL,
    ADMIN_IDS,
    CACHE_DB_PATH, CACHE_TTL_SECONDS,
    STATS_DB_PATH,
    MAX_IMAGE_DOWNLOAD_MB, ZIP_PART_MAX_MB, MAX_ZIP_IMAGES_TOTAL,
    DEVELOPER_TAG
)

from services.api_client import ApiClient
from services.cache import SqliteCache
from services.loader import spinner
from services.stats import StatsDB
from services.access import check_force_join, is_admin
from services.zip_builder import build_zip_parts

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

api = ApiClient(API_ALL_ENDPOINT, timeout=45)
cache = SqliteCache(CACHE_DB_PATH, ttl_seconds=CACHE_TTL_SECONDS)
stats = StatsDB(STATS_DB_PATH)

URL_RE = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)
USER_LAST_URL = {}   # user_id -> fb_url
USER_LAST_DATA = {}  # user_id -> last fetched data (for quick actions)

def extract_first_url(text: str) -> str:
    m = URL_RE.search(text or "")
    return m.group(1) if m else ""

def is_facebook_url(url: str) -> bool:
    t = (url or "").lower()
    return "facebook.com" in t and (t.startswith("http://") or t.startswith("https://"))

def force_join_block(chat_id: int, user_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Join Channel", url=CHANNEL_JOIN_URL),
        InlineKeyboardButton("🔄 I've Joined", callback_data="recheck_join")
    )
    bot.send_message(
        chat_id,
        "<b>🔒 Access Required</b>\n\n"
        "To use this bot, please join our channel first.\n\n"
        f"Developer: <b>{DEVELOPER_TAG}</b>",
        reply_markup=kb
    )

def must_join(user_id: int) -> bool:
    return not check_force_join(bot, REQUIRED_CHANNEL, user_id)

def menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🧑 Profile (HD)", callback_data="profile_hd"),
        InlineKeyboardButton("🖼 Cover (HD)", callback_data="cover_hd"),
    )
    kb.row(
        InlineKeyboardButton("🧩 Album 10", callback_data="album_10"),
        InlineKeyboardButton("🧩 Album 20", callback_data="album_20"),
        InlineKeyboardButton("🧩 Album 40", callback_data="album_40"),
    )
    kb.row(
        InlineKeyboardButton("📦 ZIP (Size-safe)", callback_data="zip"),
        InlineKeyboardButton("🔁 Change URL", callback_data="change_url"),
    )
    kb.row(
        InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        InlineKeyboardButton("👑 Admin", callback_data="admin"),
    )
    return kb

def help_text() -> str:
    return (
        "<b>How to use</b>\n\n"
        "• Send any Facebook profile URL\n"
        "• Use buttons to get:\n"
        "  - Profile photo (HD)\n"
        "  - Cover photo (HD)\n"
        "  - Album (10/20/40)\n"
        "  - ZIP (auto split by size)\n\n"
        "<b>Inline mode</b>\n"
        "Type in any chat:\n"
        "<code>@YourBotUsername https://www.facebook.com/zuck</code>\n\n"
        f"Developer: <b>{DEVELOPER_TAG}</b>"
    )

def admin_kb():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("📁 Export Users (CSV)", callback_data="admin_export"),
    )
    kb.row(
        InlineKeyboardButton("🧾 Logs (last 50)", callback_data="admin_logs"),
        InlineKeyboardButton("🩺 API Health", callback_data="admin_health"),
    )
    kb.row(
        InlineKeyboardButton("🔐 Force Join ON/OFF", callback_data="admin_force"),
        InlineKeyboardButton("🛠 Maintenance ON/OFF", callback_data="admin_maint"),
    )
    kb.row(
        InlineKeyboardButton("🧹 Purge Cache", callback_data="admin_cache"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
    )
    kb.row(InlineKeyboardButton("⬅️ Back", callback_data="back"))
    return kb

def fetch_profile_data(fb_url: str):
    stats.inc("requests", 1)
    cached = cache.get(fb_url)
    if cached and cached.get("success"):
        stats.inc("cache_hits", 1)
        return cached

    data = api.fetch(fb_url)
    if data and data.get("success"):
        cache.set(fb_url, data)
    return data

def send_album(chat_id: int, data: dict, count: int):
    photos = data.get("photos", []) or []
    media = [InputMediaPhoto(u) for u in photos[:count] if u]
    if not media:
        bot.send_message(chat_id, "No public photos found.", reply_markup=menu_kb())
        return
    bot.send_media_group(chat_id, media)
    stats.inc("albums_sent", 1)
    bot.send_message(
        chat_id,
        f"✅ <b>Album sent</b> (<b>{len(media)}</b> images)\n"
        f"Total found: <b>{data.get('total_count', 0)}</b>\n\n"
        f"Developer: <b>{DEVELOPER_TAG}</b>",
        reply_markup=menu_kb()
    )

def worker_action(chat_id: int, user_id: int, action: str):
    if must_join(user_id):
        force_join_block(chat_id, user_id)
        return

    fb_url = USER_LAST_URL.get(user_id)
    if not fb_url:
        bot.send_message(chat_id, "🔗 Send a Facebook URL first.", reply_markup=menu_kb())
        return

    loading = bot.send_message(chat_id, spinner(0, "Working"))
    msg_id = loading.message_id

    for step in range(1, 4):
        try:
            bot.edit_message_text(spinner(step, "Working"), chat_id, msg_id)
        except Exception:
            pass
        time.sleep(0.25)

    data = USER_LAST_DATA.get(user_id)
    if not data or not data.get("success"):
        data = fetch_profile_data(fb_url)
        USER_LAST_DATA[user_id] = data

    if not data or not data.get("success"):
        err = (data or {}).get("message") or (data or {}).get("error") or "Failed to fetch profile."
        try:
            bot.edit_message_text(
                f"❌ <b>Failed</b>\n\n{err}\n\nTry another public profile.\n\nDeveloper: <b>{DEVELOPER_TAG}</b>",
                chat_id, msg_id, reply_markup=menu_kb()
            )
        except Exception:
            bot.send_message(chat_id, f"❌ Failed: {err}", reply_markup=menu_kb())
        return

    try:
        if action == "profile_hd":
            url = data.get("profile_picture", {}).get("hd") or data.get("profile_picture", {}).get("standard")
            bot.delete_message(chat_id, msg_id)
            if url:
                bot.send_photo(chat_id, url, caption=f"🧑 <b>Profile Picture (HD)</b>\nDeveloper: <b>{DEVELOPER_TAG}</b>", reply_markup=menu_kb())
                stats.inc("profile_sent", 1)
            else:
                bot.send_message(chat_id, "No profile picture found.", reply_markup=menu_kb())

        elif action == "cover_hd":
            url = data.get("cover_photo", {}).get("hd") or data.get("cover_photo", {}).get("standard")
            bot.delete_message(chat_id, msg_id)
            if url:
                bot.send_photo(chat_id, url, caption=f"🖼 <b>Cover Photo (HD)</b>\nDeveloper: <b>{DEVELOPER_TAG}</b>", reply_markup=menu_kb())
                stats.inc("cover_sent", 1)
            else:
                bot.send_message(chat_id, "No cover photo found.", reply_markup=menu_kb())

        elif action.startswith("album_"):
            bot.delete_message(chat_id, msg_id)
            count = int(action.split("_")[1])
            send_album(chat_id, data, count)

        elif action == "zip":
            bot.edit_message_text(spinner(6, "Building ZIP (size-safe split)"), chat_id, msg_id)

            all_images = data.get("all_images", []) or []
            zip_parts, added, skipped = build_zip_parts(
                urls=all_images,
                timeout=REQUEST_TIMEOUT,
                max_total_images=MAX_ZIP_IMAGES_TOTAL,
                max_each_mb=MAX_IMAGE_DOWNLOAD_MB,
                part_max_mb=ZIP_PART_MAX_MB
            )

            bot.delete_message(chat_id, msg_id)

            if added == 0 or not zip_parts:
                bot.send_message(chat_id, "❌ Could not build ZIP (maybe blocked/private).", reply_markup=menu_kb())
                return

            stats.inc("zips_generated", 1)

            # Send each ZIP part
            for i, zbytes in enumerate(zip_parts, start=1):
                filename = f"facebook_images_part_{i}.zip" if len(zip_parts) > 1 else "facebook_images.zip"
                bot.send_document(
                    chat_id,
                    (filename, zbytes),
                    caption=(
                        f"📦 <b>ZIP Part {i}/{len(zip_parts)}</b>\n"
                        f"Added so far: <b>{added}</b> | Skipped: <b>{skipped}</b>\n"
                        f"Developer: <b>{DEVELOPER_TAG}</b>"
                    )
                )

            bot.send_message(chat_id, "✅ Done. Send another URL anytime.", reply_markup=menu_kb())

        else:
            bot.delete_message(chat_id, msg_id)
            bot.send_message(chat_id, "Unknown action.", reply_markup=menu_kb())

    except Exception:
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, "⚠️ Something went wrong. Please try again.", reply_markup=menu_kb())

def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back"))
    return kb

# ───────────── START ─────────────
@bot.message_handler(commands=["start"])
def start(message):
    stats.touch_user(message.from_user.id)

    if must_join(message.from_user.id):
        force_join_block(message.chat.id, message.from_user.id)
        return

    bot.send_message(
        message.chat.id,
        "<b>👋 Welcome!</b>\n\n"
        "Send a <b>Facebook profile URL</b> and use the menu.\n\n"
        "Example:\n<code>https://www.facebook.com/zuck</code>\n\n"
        f"Developer: <b>{DEVELOPER_TAG}</b>",
        reply_markup=menu_kb()
    )

# ───────────── CALLBACKS ─────────────
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    stats.touch_user(user_id)

    if call.data == "recheck_join":
        if must_join(user_id):
            bot.answer_callback_query(call.id, "Still not joined. Please join first.")
            return
        bot.answer_callback_query(call.id, "Access granted ✅")
        bot.send_message(chat_id, "✅ Access granted! Now send a Facebook URL.", reply_markup=menu_kb())
        return

    if call.data == "help":
        bot.edit_message_text(help_text(), chat_id, call.message.message_id, reply_markup=back_kb())
        bot.answer_callback_query(call.id)
        return

    if call.data == "back":
        bot.edit_message_text("✅ <b>Menu</b>\n\nSend a Facebook URL anytime.", chat_id, call.message.message_id, reply_markup=menu_kb())
        bot.answer_callback_query(call.id)
        return

    if call.data == "change_url":
        bot.send_message(chat_id, "🔗 Send a new Facebook profile URL.")
        bot.answer_callback_query(call.id)
        return

    # Admin panel entry
    if call.data == "admin":
        if not is_admin(user_id, ADMIN_IDS):
            bot.answer_callback_query(call.id, "Not authorized.")
            return
        bot.edit_message_text("👑 <b>Admin Panel</b>", chat_id, call.message.message_id, reply_markup=admin_kb())
        bot.answer_callback_query(call.id)
        return

    # Admin stats
    if call.data == "admin_stats":
        if not is_admin(user_id, ADMIN_IDS):
            bot.answer_callback_query(call.id, "Not authorized.")
            return
        users, counters = stats.get_summary()
        text = (
            "📊 <b>Bot Stats</b>\n\n"
            f"Users: <b>{users}</b>\n"
            f"Requests: <b>{counters.get('requests',0)}</b>\n"
            f"Cache hits: <b>{counters.get('cache_hits',0)}</b>\n"
            f"Profile sent: <b>{counters.get('profile_sent',0)}</b>\n"
            f"Cover sent: <b>{counters.get('cover_sent',0)}</b>\n"
            f"Albums sent: <b>{counters.get('albums_sent',0)}</b>\n"
            f"ZIP generated: <b>{counters.get('zips_generated',0)}</b>\n"
            f"Inline queries: <b>{counters.get('inline_queries',0)}</b>\n\n"
            f"Developer: <b>{DEVELOPER_TAG}</b>"
        )
        bot.send_message(chat_id, text, reply_markup=admin_kb())
        bot.answer_callback_query(call.id)
        return

    # Admin broadcast (simple)
    if call.data == "admin_broadcast":
        if not is_admin(user_id, ADMIN_IDS):
            bot.answer_callback_query(call.id, "Not authorized.")
            return
        bot.send_message(chat_id, "📢 Send broadcast like:\n<code>/broadcast Your message here</code>")
        bot.answer_callback_query(call.id)
        return

    # Actions in threads
    action = call.data
    threading.Thread(target=worker_action, args=(chat_id, user_id, action), daemon=True).start()
    bot.answer_callback_query(call.id)

# ───────────── BROADCAST COMMAND ─────────────
@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    user_id = message.from_user.id
    if not is_admin(user_id, ADMIN_IDS):
        bot.reply_to(message, "Not authorized.")
        return

    parts = (message.text or "").split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "Usage:\n<code>/broadcast Your message</code>")
        return

    text = parts[1].strip()

    # send to all known users
    import sqlite3
    from config import STATS_DB_PATH

    sent = 0
    failed = 0
    conn = sqlite3.connect(STATS_DB_PATH)
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()

    bot.reply_to(message, f"Broadcast started to {len(rows)} users...")

    for (uid,) in rows:
        try:
            bot.send_message(uid, f"📢 <b>Announcement</b>\n\n{text}\n\nDeveloper: <b>{DEVELOPER_TAG}</b>")
            sent += 1
        except Exception:
            failed += 1

    bot.send_message(message.chat.id, f"✅ Broadcast done.\nSent: {sent}\nFailed: {failed}")

# ───────────── URL INPUT ─────────────
@bot.message_handler(func=lambda m: True)
def on_message(message):
    user_id = message.from_user.id
    stats.touch_user(user_id)

    if must_join(user_id):
        force_join_block(message.chat.id, user_id)
        return

    url = extract_first_url((message.text or "").strip())
    if url and is_facebook_url(url):
        USER_LAST_URL[user_id] = url
        USER_LAST_DATA[user_id] = None
        bot.send_message(
            message.chat.id,
            f"✅ URL saved:\n<code>{url}</code>\n\nChoose an action:",
            reply_markup=menu_kb()
        )
        return

    bot.send_message(
        message.chat.id,
        "🔗 Please send a valid Facebook profile URL.\nExample: <code>https://www.facebook.com/zuck</code>\n\n"
        f"Developer: <b>{DEVELOPER_TAG}</b>",
        reply_markup=menu_kb()
    )

# ───────────── INLINE MODE ─────────────
@bot.inline_handler(func=lambda q: True)
def inline_handler(inline_query):
    stats.inc("inline_queries", 1)
    user_id = inline_query.from_user.id

    # Force join for inline: show instruction result
    if must_join(user_id):
        r = InlineQueryResultArticle(
            id="join_required",
            title="🔒 Join required to use inline",
            description="Tap to get join instructions",
            input_message_content=InputTextMessageContent(
                f"🔒 Please join the channel first: {CHANNEL_JOIN_URL}\nDeveloper: {DEVELOPER_TAG}"
            )
        )
        bot.answer_inline_query(inline_query.id, [r], cache_time=1, is_personal=True)
        return

    text = (inline_query.query or "").strip()
    url = extract_first_url(text)

    if not (url and is_facebook_url(url)):
        r = InlineQueryResultArticle(
            id="help",
            title="Paste a Facebook profile URL",
            description="Example: https://www.facebook.com/zuck",
            input_message_content=InputTextMessageContent(
                "Send inline like:\n@YourBotUsername https://www.facebook.com/zuck\n\nDeveloper: " + DEVELOPER_TAG
            )
        )
        bot.answer_inline_query(inline_query.id, [r], cache_time=1, is_personal=True)
        return

    # fetch quickly (cache helps)
    data = fetch_profile_data(url)
    if not data or not data.get("success"):
        msg = (data or {}).get("message") or "Failed to fetch profile (maybe private)."
        r = InlineQueryResultArticle(
            id="failed",
            title="❌ Failed to fetch",
            description=msg,
            input_message_content=InputTextMessageContent(f"❌ {msg}\nDeveloper: {DEVELOPER_TAG}")
        )
        bot.answer_inline_query(inline_query.id, [r], cache_time=1, is_personal=True)
        return

    profile = data.get("profile_picture", {}).get("hd") or data.get("profile_picture", {}).get("standard")
    cover = data.get("cover_photo", {}).get("hd") or data.get("cover_photo", {}).get("standard")
    total = data.get("total_count", 0)

    # Inline results as “articles” (safe)
    results = []

    results.append(
        InlineQueryResultArticle(
            id="r1",
            title="🧑 Profile Picture (HD)",
            description="Send profile photo link",
            input_message_content=InputTextMessageContent(
                f"🧑 Profile (HD):\n{profile}\n\nTotal images found: {total}\nDeveloper: {DEVELOPER_TAG}"
            )
        )
    )
    if cover:
        results.append(
            InlineQueryResultArticle(
                id="r2",
                title="🖼 Cover Photo (HD)",
                description="Send cover photo link",
                input_message_content=InputTextMessageContent(
                    f"🖼 Cover (HD):\n{cover}\n\nTotal images found: {total}\nDeveloper: {DEVELOPER_TAG}"
                )
            )
        )

    bot.answer_inline_query(inline_query.id, results, cache_time=5, is_personal=True)

print("🤖 Bot v3 running...")
bot.infinity_polling(skip_pending=True)
