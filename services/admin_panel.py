from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_kb(force_join: bool, maintenance: bool):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(f"🔒 Force-Join: {'ON' if force_join else 'OFF'}", callback_data="adm_toggle_force"),
        InlineKeyboardButton(f"🛠 Maintenance: {'ON' if maintenance else 'OFF'}", callback_data="adm_toggle_maint"),
    )
    kb.row(
        InlineKeyboardButton("🧹 Cache Purge", callback_data="adm_cache_purge"),
        InlineKeyboardButton("📄 Export Users CSV", callback_data="adm_export_users"),
    )
    kb.row(
        InlineKeyboardButton("🧾 Last 50 Errors", callback_data="adm_logs"),
        InlineKeyboardButton("❤️ API Health Check", callback_data="adm_health"),
    )
    return kb
