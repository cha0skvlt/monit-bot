#!/usr/bin/env python3
import os
import threading
import time
from datetime import datetime

from dotenv import load_dotenv
from telegram import ChatAction, Update
from telegram.ext import CallbackContext, CommandHandler, Updater
from core import (
    check_sites,
    check_ssl,
    load_sites,
    save_sites,
    load_status,
    save_status,
    daily_ssl_loop,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def with_typing(func):
    def wrapper(update: Update, context: CallbackContext):
        update.message.chat.send_action(action=ChatAction.TYPING)
        return func(update, context)
    return wrapper

@with_typing
def cmd_status(update: Update, ctx: CallbackContext):
    check_sites()
    status = load_status()
    sites = load_sites()
    lines = ["🌐 Site status:"]
    for site in sites:
        data = status.get(site, {"down_since": None})
        down_since = data.get("down_since")

        if down_since:
            try:
                ts = datetime.fromisoformat(down_since)
                formatted = ts.strftime("%Y-%m-%d (%H:%M)")
            except Exception:
                formatted = down_since
            lines.append(f"🔴 {site} — DOWN since {formatted}")
        else:
            lines.append(f"🟢 {site} — OK")

    update.message.reply_text("\n".join(lines), disable_web_page_preview=True)

@with_typing
def cmd_list(update: Update, ctx: CallbackContext):
    update.message.reply_text(
        "🔗 Monitored sites:\n" + "\n".join(load_sites()),
        disable_web_page_preview=True,
    )

@with_typing
def cmd_add(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text(
            "Usage: /add https://example.com",
            disable_web_page_preview=True,
        )
        return
    site = ctx.args[0]
    sites = load_sites()
    if site in sites:
        update.message.reply_text(
            "Site already added.",
            disable_web_page_preview=True,
        )
    else:
        sites.append(site)
        save_sites(sites)
        update.message.reply_text(
            "✅ Added.",
            disable_web_page_preview=True,
        )

@with_typing
def cmd_remove(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text(
            "Usage: /remove https://example.com",
            disable_web_page_preview=True,
        )
        return
    site = ctx.args[0]
    sites = load_sites()
    if site not in sites:
        update.message.reply_text(
            "Site not found.",
            disable_web_page_preview=True,
        )
    else:
        sites.remove(site)
        save_sites(sites)
        status = load_status()
        status.pop(site, None)
        save_status(status)
        update.message.reply_text("❌ Removed.", disable_web_page_preview=True)

@with_typing
def cmd_ssl_check(update: Update, ctx: CallbackContext):
    update.message.reply_text(check_ssl(), disable_web_page_preview=True)

@with_typing
def cmd_start(update: Update, ctx: CallbackContext):
    update.message.reply_text("""🤖 Web monitoring bot:

🕘 SSL auto-check runs daily at 06:00 UTC.
⚠️ Alerts if any cert expires in ≤ 7 days.
🚨 Site downtime alerts: first at 3 min, then hourly.
➕ Sites are managed via Telegram.
📄 Logs formatted for Grafana or external analysis.

🖥️ Commands:
/status  — current site states
/ssl     — manual SSL check
/list    — list of monitored URLs
/add     — add site
/remove  — remove site
""", disable_web_page_preview=True)


def background_loop():
    while True:
        try:
            t = time.gmtime()
            check_sites()
            if t.tm_hour == 3 and t.tm_min == 0:
                check_ssl()
        except Exception as e:
            print(f"[background_loop error] {e}")
        time.sleep(60)

def start_bot():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", cmd_status))
    dp.add_handler(CommandHandler("list", cmd_list))
    dp.add_handler(CommandHandler("add", cmd_add))
    dp.add_handler(CommandHandler("remove", cmd_remove))
    dp.add_handler(CommandHandler("ssl", cmd_ssl_check))
    dp.add_handler(CommandHandler("start", cmd_start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=background_loop, daemon=True).start()
    threading.Thread(target=daily_ssl_loop, daemon=True).start()
    start_bot()
