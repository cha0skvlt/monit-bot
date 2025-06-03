# 🛡️ Web Monitor Telegram Bot  
## @cha0skvlt

Lightweight, production-ready **monitoring bot in Docker**  
Tracks **site availability** and **SSL lifetime**, sends **Telegram alerts**, and logs to file for **Grafana/ELK** dashboards.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ⚙️ Features

- 🌍 **Uptime Monitoring**  
  Checks each site every minute (HTTP status 200)  
  Alerts: after 5 min of downtime, then hourly

- 🔐 **SSL Certificate Lifetime**  
  Daily auto-check at 06:00 UTC  (09:00 Moskow)
  Alerts: if cert expires in ≤ 7 days

- 📡 **Telegram Bot Interface**  
  - `/status` — current site states  
  - `/ssl` — manual SSL check  
  - `/list` — show monitored URLs  
  - `/add URL` — add new site  
  - `/remove URL` — remove site  
  - `/help` — command summary

- 💾 **Stateful & Durable**  
  - Persistent files: `sites.txt`, `status.json`, `monitor.log`  
  - Autostart: Docker `restart: always`

- 📄 **Structured Logging**  
  - Logs in JSON format for external analysis  
  - Compatible with **Grafana Loki**, ELK, or custom scripts

---

## 🚀 Quickstart

```bash
git clone https://github.com/YOURUSER/telegram-site-monitor.git
cd telegram-site-monitor

cp .env.example .env  # insert your BOT_TOKEN and CHAT_ID

docker compose up --build -d
```

### Running tests

```bash
pip install -r requirements.txt
pytest
```
