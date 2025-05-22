# 🛡️ Telegram Site Monitor
## @cha0skvlt

Minimal, production-ready **Dockerized monitoring bot** for checking website availability and SSL expiration.  
Sends alerts directly to Telegram. Lightweight. Clean. Perfect for personal or business use.

![Docker](https://img.shields.io/badge/docker-ready-blue) ![Python](https://img.shields.io/badge/python-3.11+-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🚀 Features

- 🌐 **Uptime check** every minute (HTTP 200 validation)
- 🔐 **SSL expiration** alert daily (7-day warning)
- 🤖 **Telegram Bot Interface**
  - `/status` — show all site statuses
  - `/list` — list monitored URLs
  - `/add https://example.com` — add a site
  - `/remove https://example.com` — remove a site
  - `/ssl` — manual SSL cert check
  - `/help` — all commands
- 💾 Persistent state in `status.json`
- 🔁 Auto-restart with `restart: always`
- 🧱 Modular structure: `core.py` (logic), `bot.py` (interface)

---

## ⚙️ Quickstart

```bash
git clone https://github.com/YOURUSER/telegram-site-monitor.git
cd telegram-site-monitor

cp .env.example .env  # Add your BOT_TOKEN and CHAT_ID

docker compose up --build -d
