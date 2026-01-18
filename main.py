import os
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🤖 <b>Bot is LIVE on Choreo!</b>\n\n"
        "Send a Facebook profile URL to begin.\n\n"
        "Developer: @mrseller_00"
    )

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "✅ Bot is running correctly.")

print("🤖 Bot started successfully")

bot.infinity_polling(skip_pending=True)
