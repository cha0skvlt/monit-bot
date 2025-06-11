# 🤖 Web Monitor Bot

Telegram bot that checks website uptime and SSL expiration. Designed for Docker, it
stores data in SQLite and writes structured logs.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- Periodic uptime checks with retry logic
- Daily SSL certificate monitoring
- Admin commands for managing sites and admins
- Stores data and logs in SQLite
- Docker setup with healthcheck

## Quick start

1. Clone the repo and copy `.env.example` to `.env`.
2. Set `BOT_TOKEN`, `CHAT_ID`, `ADMIN_IDS` and `OWNER_ID`.
3. Build and run the container:

   ```bash
   docker compose up --build -d
   ```

Optional variables `DB_FILE`, `LOG_FILE` and `REQUEST_TIMEOUT` change paths and
timeouts. If `DB_FILE` is a directory, the bot creates `db.sqlite` inside it.

## Usage

Interact with the bot via Telegram:

- `/add <url>` – start monitoring
- `/rem <url>` – stop monitoring
- `/status` – current status
- `/checkssl` – check SSL now
- `/list` – list sites
- `/add_admin <id>` – grant admin rights
- `/rm_admin <id>` – revoke admin rights
- `/help` – show help

## Русская версия

See [`docs/guide_ru.md`](docs/guide_ru.md) for the Russian manual.

Made by [@cha0skvlt](https://github.com/cha0skvlt). Star the repo!
