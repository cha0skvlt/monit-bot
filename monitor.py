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

from datetime import datetime

def cmd_status(update: Update, ctx: CallbackContext):
    check_sites()
    status = load_status()
    lines = ["🔁 Актуальный статус:"]
    for site, data in status.items():
        if data["down_since"]:
            try:
                ts = datetime.fromisoformat(data["down_since"])
                formatted = ts.strftime("%Y-%m-%d %H:%M")
            except:
                formatted = data["down_since"]
            lines.append(f"🔴 {site} — down с {formatted}")
        else:
            lines.append(f"🟢 {site} — OK")
    update.message.reply_text("\n".join(lines), disable_web_page_preview=True)

def cmd_list(update: Update, ctx: CallbackContext):
    sites = load_sites()
    update.message.reply_text("🔗 Сайты:\n" + "\n".join(sites), disable_web_page_preview=True)

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

def cmd_ssl_check(update: Update, ctx: CallbackContext):
    result = check_ssl()
    update.message.reply_text(result, disable_web_page_preview=True)

def cmd_help(update: Update, ctx: CallbackContext):
    update.message.reply_text("""📟 Команды:
/status — статус сайтов
/ssl — проверить SSL

/list — список сайтов
/add URL — добавить
/remove URL — удалить

/help — справка
""", disable_web_page_preview=True)

def background_loop():
    while True:
        t = time.gmtime()
        check_sites()
        if t.tm_hour == 3 and t.tm_min == 0:
            check_ssl()
        time.sleep(60)

def start_bot():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", cmd_status))
    dp.add_handler(CommandHandler("list", cmd_list))
    dp.add_handler(CommandHandler("add", cmd_add))
    dp.add_handler(CommandHandler("remove", cmd_remove))
    dp.add_handler(CommandHandler("ssl", cmd_ssl_check))
    dp.add_handler(CommandHandler("help", cmd_help))
    updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=background_loop, daemon=True).start()
    start_bot()