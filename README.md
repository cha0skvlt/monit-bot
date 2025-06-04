# 🛡️ Web Monitor Telegram Bot

A minimal yet production-ready bot that checks websites for uptime and SSL certificate expiration. Alerts are delivered to Telegram and all events are stored in structured JSON logs. The bot is designed to run in Docker with persistent state.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- 🌍 **Uptime Monitoring** – each site is checked every minute in parallel. If a site stays down for 5 minutes you get a notification and then hourly reminders until it recovers.
- 🔐 **SSL Certificate Lifetime** – certificates are verified daily at 06:00 UTC and on demand. Alerts are sent if any certificate expires in seven days or less.
- 📡 **Telegram Commands** – manage the monitored list directly in chat: `/status`, `/ssl`, `/list`, `/add URL`, `/remove URL` and `/start` for help.
- 💾 **Durable State** – URLs, status and logs are kept on disk (`sites.txt`, `status.json`, `monitor.log`). Paths can be customized via the `SITES_FILE`, `STATUS_FILE` and `LOG_FILE` variables.
- 📄 **Structured Logging** – events are written in JSON so they can be easily processed by Grafana Loki, ELK or other tools.
- 📴 **Graceful Startup** – the bot skips checks when no sites are configured.
- 📈 **Instant Status Updates** – the `/status` command reflects additions and removals immediately.
- ✅ **Strict HTTP 200 check** – a site is marked OK only when it returns HTTP 200.


## Setup

1. Clone this repository.
2. Copy `.env.example` to `.env` and fill in `BOT_TOKEN` and `CHAT_ID`.
3. Create an empty state file:

   ```bash
   echo '{}' > status.json
   ```
4. Build and start the container:
=======
   Optional variables `SITES_FILE`, `STATUS_FILE` and `LOG_FILE` allow
   changing paths to the data files.
3. Build and start the container:


   ```bash
   docker compose up --build -d
   ```

   `status.json` must exist before running `docker compose up`. The compose file mounts the data files and restarts the bot automatically.


## 📚 Документация на русском

Более подробное руководство по настройке и работе проекта находится в файле
[`docs/guide_ru.md`](docs/guide_ru.md).


### Running tests

```bash
pip install -r requirements.txt
pytest -q
```
