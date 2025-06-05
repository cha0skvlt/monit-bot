# 🤖 Web Monitor Bot

Minimal Telegram bot that checks your sites every minute and warns about expiring SSL certificates.
Runs in Docker, stores data in SQLite and logs in JSON.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- Uptime alerts after 3 minutes of downtime
- Multi-stage checks avoid DNS caching errors
- Daily SSL certificate check
- Manage URLs via Telegram `/status`, `/ssl`, `/list`, `/add`, `/remove`
- All data in a single SQLite file

## Quick start

1. Clone this repository.
2. Copy `.env.example` to `.env` and fill in `BOT_TOKEN` and `CHAT_ID`.
3. Run `./telegram_test.sh` to verify your credentials.
4. Build and start the container:

    ```bash
    docker compose up --build -d
    ```

    The container creates the SQLite database on first run. Optional variables
    `DB_FILE`, `LOG_FILE` and `REQUEST_TIMEOUT` tune paths and request timeout.
    If `DB_FILE` is a directory or a non-existent path without extension, the
    file `db.sqlite` will be created inside it. A plain filename will place the
    database in the current working directory.

    If `DB_FILE` points to a directory, the file `db.sqlite` will be created
    inside it.



## Документация на русском

Более подробное руководство по настройке и работе проекта находится в файле
[`docs/guide_ru.md`](docs/guide_ru.md).


Made by [@cha0skvlt](https://github.com/cha0skvlt). Star the repo if it helps you!
