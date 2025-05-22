#!/usr/bin/env python3
import time, threading, json, os
from main import check_sites, check_ssl, load_sites, save_sites, load_status, save_status, send_alert
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SITES_FILE = "/app/sites.txt"
STATUS_FILE = "/app/status.json"

# ────────────────────────────────────────────────────────────────────────────────
# Telegram Command Handlers

def cmd_status(update: Update, ctx: CallbackContext):
    status = load_status()
    text = ""
    for site, data in status.items():
        if data["down_since"]:
            text += f"🔴 {site} — down с {data['down_since']}\n"
        else:
            text += f"🟢 {site} — OK\n"
    update.message.reply_text(text or "Список пуст.")

def cmd_list(update: Update, ctx: CallbackContext):
    sites = load_sites()
    update.message.reply_text("🔗 Сайты:\n" + "\n".join(sites))

def cmd_add(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text("Формат: /add https://example.com")
        return
    site = ctx.args[0]
    sites = load_sites()
    if site in sites:
        update.message.reply_text("Сайт уже есть.")
    else:
        sites.append(site)
        save_sites(sites)
        update.message.reply_text("✅ Добавлено.")

def cmd_remove(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text("Формат: /remove https://example.com")
        return
    site = ctx.args[0]
    sites = load_sites()
    if site not in sites:
        update.message.reply_text("Сайта нет.")
    else:
        sites.remove(site)
        save_sites(sites)
        status = load_status()
        status.pop(site, None)
        save_status(status)
        update.message.reply_text("❌ Удалено.")

def cmd_force_check(update: Update, ctx: CallbackContext):
    check_sites()
    update.message.reply_text("🔁 Проверка запущена.")

def cmd_ssl_check(update: Update, ctx: CallbackContext):
    check_ssl()
    update.message.reply_text("🔐 SSL проверка запущена.")

def cmd_help(update: Update, ctx: CallbackContext):
    update.message.reply_text("""📟 Команды:
/status — статус сайтов
/list — список сайтов
/add URL — добавить
/remove URL — удалить
/force_check — проверить доступность
/ssl_check — проверить SSL
/help — справка""")

# ────────────────────────────────────────────────────────────────────────────────
# Фоновая проверка

def background_loop():
    while True:
        t = time.gmtime()
        check_sites()
        if t.tm_hour == 3 and t.tm_min == 0:
            check_ssl()
        time.sleep(60)

# ────────────────────────────────────────────────────────────────────────────────
# Запуск

def start_bot():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", cmd_status))
    dp.add_handler(CommandHandler("list", cmd_list))
    dp.add_handler(CommandHandler("add", cmd_add))
    dp.add_handler(CommandHandler("remove", cmd_remove))
    dp.add_handler(CommandHandler("force_check", cmd_force_check))
    dp.add_handler(CommandHandler("ssl_check", cmd_ssl_check))
    dp.add_handler(CommandHandler("help", cmd_help))
    updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=background_loop, daemon=True).start()
    start_bot()
