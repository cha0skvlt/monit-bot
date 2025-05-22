# 🛡️ Telegram Site Monitor

Minimal, production-ready **Dockerized monitoring bot** for checking website availability and SSL expiration.  
Sends alerts directly to Telegram. Lightweight. Battle-tested. Perfect for personal or business use.

![Docker](https://img.shields.io/badge/docker-ready-blue) ![Python](https://img.shields.io/badge/python-3.11+-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🚀 Features

- 🌐 **Uptime check** every minute (HTTP 200 validation)
- 🔐 **SSL expiration** alert daily (7-day warning)
- 🧠 **Telegram Bot Interface**
  - `/status` — see all sites with their current state
  - `/list` — list monitored URLs
  - `/add https://example.com` — add a site
  - `/remove https://example.com` — remove a site
  - `/force_check` — trigger instant check
  - `/ssl_check` — trigger SSL scan
  - `/help` — command reference
- 💾 Persistent state (JSON-based)
- 🔁 Auto-restart container with `restart: always`

---

## ⚙️ Quickstart

```bash
git clone https://github.com/YOURUSER/telegram-site-monitor.git
cd telegram-site-monitor

cp .env.example .env  # Add your Telegram bot token and chat ID

docker-compose up --build -d
