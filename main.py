import threading
import time
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

import config
from services.state import RuntimeState
from services.cache import TTLCache
from services.logger_ring import RingLogger
from services.api_client import fetch_all
from services.zip_builder import build_zip_parts
from services.export_csv import export_users_csv
from services.admin_panel import admin_kb
from services.web_health import make_app

if not config.BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

state = RuntimeState(force_join=config.DEFAULT_FORCE_JOIN, maintenance=config.DEFAULT_MAINTENANCE)
cache = TTLCache(ttl_sec=config.CACHE_TTL_SEC)
ringlog = RingLogger(maxlen=50)

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")

def is_admin(uid: int) -> bool:
    return uid in config.ADMIN_IDS

def need_join(uid: int) -> bool:
    if not state.force_join:
        return False
    if not config.REQUIRED_CHANNEL:
        return False
    try:
        m = bot.get_chat_member(config.REQUIRED_CHANNEL, uid)
        return m.status not in ("member", "administrator", "creator")
    except Exception:
        return True

def join_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Join Channel", url=config.CHANNEL_JOIN_URL or "https://t.me/"))
    kb.add(InlineKeyboardButton("🔄 I've Joined", callback_data="recheck_join"))
    return kb

def main_kb():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🧑 Profile HD", callback_data="profile_hd"),
        InlineKeyboardButton("🖼 Cover HD", callback_data="cover_hd"),
    )
    kb.row(
        InlineKeyboardButton("🧩 Album 10", callback_data="album_10"),
        InlineKeyboardButton("🧩 Album 20", callback_data="album_20"),
        InlineKeyboardButton("🧩 Album 40", callback_data="album_40"),
    )
    kb.row(
        InlineKeyboardButton("📦 Smart ZIP (split)", callback_data="zip_split"),
        InlineKeyboardButton("🧭 Admin", callback_data="admin") ,
    )
    kb.row(
        InlineKeyboardButton("ℹ️ Help", callback_data="help"),
    )
    return kb

def safe_reply(chat_id, text, **kw):
    try:
        return bot.send_message(chat_id, text, **kw)
    except Exception as e:
        ringlog.add("ERROR", f"send_message failed: {e}")

def call_api(fb_url: str):
    # cache by URL
    cached = cache.get(fb_url)
    if cached:
        return cached
    if not config.API_ALL_ENDPOINT:
        return None
    data = fetch_all(config.API_ALL_ENDPOINT, fb_url)
    if data and data.get("success"):
        cache.set(fb_url, data)
    return data

@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    if state.maintenance and (not is_admin(uid)):
        safe_reply(m.chat.id, "🛠 <b>Maintenance mode</b>\nTry again later.")
        return
    if need_join(uid):
        safe_reply(m.chat.id, "🔒 <b>Join required</b> to use this bot.", reply_markup=join_kb())
        return

    safe_reply(
        m.chat.id,
        "🤖 <b>GADGET ADVANCE TOOLS</b>\n"
        "Send a Facebook profile URL.\n\n"
        "Developer: <b>@mrseller_00</b>",
        reply_markup=main_kb()
    )

@bot.callback_query_handler(func=lambda c: c.data == "recheck_join")
def recheck_join(c):
    uid = c.from_user.id
    if need_join(uid):
        bot.answer_callback_query(c.id, "Still not joined.")
        return
    bot.answer_callback_query(c.id, "Access granted ✅")
    safe_reply(c.message.chat.id, "Now send a Facebook URL.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: bool(m.text) and ("facebook.com" in m.text.lower()))
def got_url(m):
    uid = m.from_user.id
    if state.maintenance and (not is_admin(uid)):
        safe_reply(m.chat.id, "🛠 <b>Maintenance mode</b>\nTry again later.")
        return
    if need_join(uid):
        safe_reply(m.chat.id, "🔒 <b>Join required</b> to use this bot.", reply_markup=join_kb())
        return

    url = m.text.strip()
    state.save_url(uid, url)
    safe_reply(m.chat.id, "✅ URL saved. Choose an option:", reply_markup=main_kb())

@bot.callback_query_handler(func=lambda c: True)
def on_click(c):
    uid = c.from_user.id

    # Admin panel open
    if c.data == "admin":
        if not is_admin(uid):
            bot.answer_callback_query(c.id, "Not admin.")
            return
        bot.answer_callback_query(c.id)
        safe_reply(
            c.message.chat.id,
            "🧭 <b>Admin Panel</b>",
            reply_markup=admin_kb(state.force_join, state.maintenance)
        )
        return

    # Admin actions
    if c.data.startswith("adm_"):
        if not is_admin(uid):
            bot.answer_callback_query(c.id, "Not admin.")
            return

        if c.data == "adm_toggle_force":
            state.set_force_join(not state.force_join)
            bot.answer_callback_query(c.id, "Updated")
            safe_reply(c.message.chat.id, "Updated ✅", reply_markup=admin_kb(state.force_join, state.maintenance))
            return

        if c.data == "adm_toggle_maint":
            state.set_maintenance(not state.maintenance)
            bot.answer_callback_query(c.id, "Updated")
            safe_reply(c.message.chat.id, "Updated ✅", reply_markup=admin_kb(state.force_join, state.maintenance))
            return

        if c.data == "adm_cache_purge":
            cache.purge()
            bot.answer_callback_query(c.id, "Cache purged")
            safe_reply(c.message.chat.id, "🧹 Cache purged ✅", reply_markup=admin_kb(state.force_join, state.maintenance))
            return

        if c.data == "adm_export_users":
            csv_bytes = export_users_csv(state.users_seen)
            bot.answer_callback_query(c.id, "Exporting…")
            bot.send_document(c.message.chat.id, ("users.csv", csv_bytes), caption="📄 Users export")
            return

        if c.data == "adm_logs":
            logs = ringlog.tail(50)
            bot.answer_callback_query(c.id, "Showing logs")
            text = "<b>🧾 Last 50 errors</b>\n\n" + ("\n".join(logs) if logs else "No errors ✅")
            safe_reply(c.message.chat.id, text[:3800])  # telegram limit guard
            return

        if c.data == "adm_health":
            bot.answer_callback_query(c.id, "Checking…")
            ok = False
            detail = ""
            if config.API_ALL_ENDPOINT:
                try:
                    # health endpoint may not exist; try HEAD/GET base
                    r = requests.get(config.API_ALL_ENDPOINT, timeout=15)
                    ok = (r.status_code < 500)
                    detail = f"HTTP {r.status_code}"
                except Exception as e:
                    detail = str(e)
            safe_reply(c.message.chat.id, f"❤️ API Health: <b>{'OK' if ok else 'FAIL'}</b>\n{detail}")
            return

    # Non-admin / general actions
    if state.maintenance and (not is_admin(uid)):
        bot.answer_callback_query(c.id, "Maintenance")
        return
    if need_join(uid):
        bot.answer_callback_query(c.id, "Join required")
        safe_reply(c.message.chat.id, "🔒 Join required.", reply_markup=join_kb())
        return

    if c.data == "help":
        bot.answer_callback_query(c.id)
        safe_reply(
            c.message.chat.id,
            "<b>How to use</b>\n"
            "1) Send a Facebook profile URL\n"
            "2) Choose Profile/Cover/Album/ZIP\n\n"
            "✅ Choose count: 10 / 20 / 40\n"
            "📦 ZIP will auto-split if big\n",
            reply_markup=main_kb()
        )
        return

    fb_url = state.get_url(uid)
    if not fb_url:
        bot.answer_callback_query(c.id, "Send URL first")
        return

    # Load data
    bot.answer_callback_query(c.id, "Working…")
    msg = safe_reply(c.message.chat.id, "⏳ Processing…")
    try:
        data = call_api(fb_url)
        state.bump()
    except Exception as e:
        ringlog.add("ERROR", f"API call failed: {e}")
        data = None

    try:
        if msg:
            bot.delete_message(c.message.chat.id, msg.message_id)
    except:
        pass

    if not data or not data.get("success"):
        safe_reply(c.message.chat.id, "❌ Failed to fetch. Profile may be private or blocked.", reply_markup=main_kb())
        return

    # Actions
    if c.data == "profile_hd":
        p = data.get("profile_picture", {}).get("hd")
        if p:
            bot.send_photo(c.message.chat.id, p, caption="🧑 Profile (HD)", reply_markup=main_kb())
        else:
            safe_reply(c.message.chat.id, "No profile picture found.", reply_markup=main_kb())
        return

    if c.data == "cover_hd":
        p = data.get("cover_photo", {}).get("hd")
        if p:
            bot.send_photo(c.message.chat.id, p, caption="🖼 Cover (HD)", reply_markup=main_kb())
        else:
            safe_reply(c.message.chat.id, "No cover photo found.", reply_markup=main_kb())
        return

    if c.data.startswith("album_"):
        n = int(c.data.split("_")[1])
        photos = data.get("photos", [])[:n]
        media = [InputMediaPhoto(u) for u in photos if isinstance(u, str)]
        if not media:
            safe_reply(c.message.chat.id, "No photos found.", reply_markup=main_kb())
            return
        # Telegram media group limit is 10 per group
        for i in range(0, len(media), 10):
            bot.send_media_group(c.message.chat.id, media[i:i+10])
        safe_reply(c.message.chat.id, f"✅ Album sent ({len(media)})", reply_markup=main_kb())
        return

    if c.data == "zip_split":
        urls = data.get("all_images", []) or []
        if not urls:
            safe_reply(c.message.chat.id, "No images found for ZIP.", reply_markup=main_kb())
            return

        safe_reply(c.message.chat.id, "📦 Building ZIP (auto-split)…")
        try:
            parts, files_added = build_zip_parts(urls, part_max_mb=config.ZIP_PART_MAX_MB)
        except Exception as e:
            ringlog.add("ERROR", f"zip build failed: {e}")
            safe_reply(c.message.chat.id, "ZIP failed.", reply_markup=main_kb())
            return

        if not parts:
            safe_reply(c.message.chat.id, "ZIP empty (no downloadable images).", reply_markup=main_kb())
            return

        for name, bio in parts:
            try:
                bot.send_document(c.message.chat.id, (name, bio), caption=f"📦 {name}")
            except Exception as e:
                ringlog.add("ERROR", f"send_document failed: {e}")

        safe_reply(c.message.chat.id, f"✅ ZIP done. Files: {files_added}, Parts: {len(parts)}", reply_markup=main_kb())
        return


def run_health_server():
    app = make_app(state, cache, ringlog)
    # Choreo wants a port; use 8080
    app.run(host="0.0.0.0", port=8080, debug=False)

print("🤖 Advanced Bot v5 starting…")

t = threading.Thread(target=run_health_server, daemon=True)
t.start()

# Strong polling settings to reduce API hiccups
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)
    except Exception as e:
        ringlog.add("ERROR", f"polling crashed: {e}")
        time.sleep(3)
