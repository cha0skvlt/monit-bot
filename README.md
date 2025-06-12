# 🤖 Web Monitor Bot 🜂 🜃

### V 2.0

Telegram bot that checks website uptime and SSL expiration. Designed for Docker, it
stores data in SQLite and writes structured logs.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- 🔁 Pings websites every 3 minutes to check availability
- 🕵️ SSL certificate check runs daily at 06:00 UTC
- 🚨 Alerts when a site goes down or recovers
- ⏳ Warnings 7 days before SSL certificates expire
- 📋 Telegram-based command interface
- 🗃️ SQLite for persistence
- 🐳 Docker-ready deployment

---

## 📦 Installation

```bash
git clone https://github.com/yourname/monit-bot.git
cd monit-bot
cp .env.example .env  # or create one manually
docker compose up -d
```

```.env
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=group_or_user_chat_ID
OWNER_ID=this_ID_can_manage_admins
```

---

## Usage

Interact with the bot via Telegram:

- `/add <url>` – start monitoring
- `/rem <url>` – stop monitoring
- `/status` – current status
- `/checkssl` – check SSL now
- `/list` – list sites
- `/add_admin <id>` – grant admin rights (Owner only)
- `/rm_admin <id>` – revoke admin rights (Owner only
- `/help` – show help

## Русская версия

See [`docs/guide_ru.md`](docs/guide_ru.md) for the Russian manual.

## Made [@cha0skvlt](https://github.com/cha0skvlt)

