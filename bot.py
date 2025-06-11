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
    is_valid_url,
    load_admins,
    add_admin,
    remove_admin,
    OWNER_ID,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def with_typing(func):
    def wrapper(update: Update, context: CallbackContext):
        update.message.chat.send_action(action=ChatAction.TYPING)
        return func(update, context)
    return wrapper

def admin_only(func):
    def wrapper(update: Update, ctx: CallbackContext):
        user_id = str(update.effective_user.id)
        if user_id not in load_admins():
            update.message.reply_text("Access denied.")
            return
        return func(update, ctx)
    return wrapper

@with_typing
@admin_only
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
@admin_only
def cmd_list(update: Update, ctx: CallbackContext):
    update.message.reply_text(
        "🔗 Monitored sites:\n" + "\n".join(load_sites()),
        disable_web_page_preview=True,
    )

@with_typing
@admin_only
def cmd_add(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text(
            "Usage: /add https://example.com",
            disable_web_page_preview=True,
        )
        return
    site = ctx.args[0]
    if not is_valid_url(site):
        update.message.reply_text("Invalid URL.")
        return
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
@admin_only
def cmd_remove(update: Update, ctx: CallbackContext):
    if not ctx.args:
        update.message.reply_text(
            "Usage: /rem https://example.com",
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
@admin_only

def cmd_ssl_check(update: Update, ctx: CallbackContext):

    def run():
        result = check_ssl()
        update.message.reply_text(result, disable_web_page_preview=True)

    threading.Thread(target=run).start()

def help_text(lang: str) -> str:
    if lang.startswith("ru"):
        return (
            "🤖 Бот мониторинга сайтов:\n\n"
            "🕘 Авто-проверка SSL в 06:00 UTC.\n"
            "⚠️ Оповещения за 7 дней до истечения.\n"
            "🚨 Алёрты при падении сайтов.\n\n"
            "🖥️ Команды:\n"
            "/status — состояние сайтов\n"
            "/ssl — проверка SSL\n"
            "/list — список URL\n"
            "/add — добавить сайт\n"
            "/rem — удалить сайт"

        )
    return (
        "🤖 Web monitoring bot:\n\n"
        "🕘 SSL auto-check runs daily at 06:00 UTC.\n"
        "⚠️ Alerts if any cert expires in ≤ 7 days.\n"
        "🚨 Site downtime alerts.\n\n"
        "🖥️ Commands:\n"
        "/status  — current site states\n"
        "/ssl     — manual SSL check\n"
        "/list    — list of monitored URLs\n"
        "/add     — add site\n"
        "/rem     — remove site"
    )

@with_typing
@admin_only
def cmd_help(update: Update, ctx: CallbackContext):
    lang = update.effective_user.language_code or "en"
    update.message.reply_text(help_text(lang), disable_web_page_preview=True)

@with_typing
@admin_only
def cmd_start(update: Update, ctx: CallbackContext):
    cmd_help(update, ctx)



@with_typing
@admin_only
def cmd_add_admin(update: Update, ctx: CallbackContext):
    if str(update.effective_user.id) != (OWNER_ID or ""):
        update.message.reply_text("Access denied.")
        return
    if not ctx.args:
        update.message.reply_text("Usage: /add_admin <id>")
        return
    try:
        admin_id = str(int(ctx.args[0]))
    except ValueError:
        update.message.reply_text("Invalid ID format")
        return
    add_admin(admin_id)
    update.message.reply_text("Admin added.")

@with_typing
@admin_only
def cmd_rm_admin(update: Update, ctx: CallbackContext):
    if str(update.effective_user.id) != (OWNER_ID or ""):
        update.message.reply_text("Access denied.")
        return
    if not ctx.args:
        update.message.reply_text("Usage: /rm_admin <id>")
        return
    try:
        admin_id = str(int(ctx.args[0]))
    except ValueError:
        update.message.reply_text("Invalid ID format")
        return
    remove_admin(admin_id)
    update.message.reply_text("Admin removed.")


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
    dp.add_handler(CommandHandler("rem", cmd_remove))
    dp.add_handler(CommandHandler("ssl", cmd_ssl_check))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("add_admin", cmd_add_admin))
    dp.add_handler(CommandHandler("rm_admin", cmd_rm_admin))
    dp.add_handler(CommandHandler("start", cmd_start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    threading.Thread(target=background_loop, daemon=True).start()
    threading.Thread(target=daily_ssl_loop, daemon=True).start()
    start_bot()
