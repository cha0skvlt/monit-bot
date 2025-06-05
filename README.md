# ⭐ Web Monitor Bot

Minimal Telegram bot that checks your sites every minute and warns about expiring SSL certificates.
Runs in Docker, stores data in SQLite and logs in JSON.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- Uptime alerts after 3 minutes of downtime
- Daily SSL certificate check
- Manage URLs via `/status`, `/ssl`, `/list`, `/add`, `/remove`
- All data in a single SQLite file

## Quick start

1. Copy `.env.example` to `.env` and set `BOT_TOKEN` and `CHAT_ID`.
2. Run `./telegram_test.sh` to verify the credentials.
3. `docker compose up --build -d`

`DB_FILE`, `LOG_FILE` and `REQUEST_TIMEOUT` can be changed in `.env`.

---

Made with ❤️ by [@cha0skvlt](https://github.com/cha0skvlt). Star the repo if it helps you!
