#!/usr/bin/env python3

import datetime
import json
import logging
import os
import socket
import ssl
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = os.getenv("LOG_FILE", "/app/logs/monitor.log")
DB_FILE = os.getenv("DB_FILE", "/app/db.sqlite")
if os.path.isdir(DB_FILE):
    DB_FILE = os.path.join(DB_FILE, "db.sqlite")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

LEGACY_SITES_FILE = Path("/app/sites.txt")
LEGACY_STATUS_FILE = Path("/app/status.json")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(message)s")


def init_db():
    """Create database and migrate data on first run."""
    if getattr(init_db, "done", False):
        return
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS sites (url TEXT PRIMARY KEY)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS status (site TEXT PRIMARY KEY, down_since TEXT)"
    )
    cur.execute("CREATE TABLE IF NOT EXISTS logs (data TEXT)")
    cur.execute("SELECT COUNT(*) FROM sites")
    if cur.fetchone()[0] == 0 and LEGACY_SITES_FILE.exists():
        for line in LEGACY_SITES_FILE.read_text().splitlines():
            url = line.strip()
            if url:
                cur.execute("INSERT OR IGNORE INTO sites(url) VALUES (?)", (url,))
    cur.execute("SELECT COUNT(*) FROM status")
    if cur.fetchone()[0] == 0 and LEGACY_STATUS_FILE.exists():
        try:
            data = json.loads(LEGACY_STATUS_FILE.read_text())
        except json.JSONDecodeError:
            data = {}
        for site, st in data.items():
            cur.execute(
                "INSERT OR IGNORE INTO status(site, down_since) VALUES (?, ?)",
                (site, st.get("down_since")),
            )
    conn.commit()
    conn.close()
    init_db.done = True

def log_event(data: dict):
    """Append structured JSON event to log file."""
    data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    logging.info(json.dumps(data))
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO logs(data) VALUES (?)", (json.dumps(data),))

_bot = None
_bot_lock = threading.Lock()


def _get_bot():
    global _bot
    with _bot_lock:
        if _bot is None:
            _bot = Bot(BOT_TOKEN)
        return _bot


def send_alert(msg, disable_web_page_preview=True):
    if not CHAT_ID:
        print("[send_alert] CHAT_ID not set")
        return
    try:
        _get_bot().send_message(
            chat_id=CHAT_ID,
            text=msg,
            disable_web_page_preview=disable_web_page_preview,
        )
    except Exception as e:
        print(f"[send_alert error] {e}")

def load_sites():
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT url FROM sites ORDER BY url")
        return [row[0] for row in cur.fetchall()]

def save_sites(sites):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM sites")
        conn.executemany(
            "INSERT INTO sites(url) VALUES (?)",
            [(s.strip(),) for s in sites if s.strip()],
        )
        conn.commit()

def load_status():
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT site, down_since FROM status")
        return {row[0]: {"down_since": row[1]} for row in cur.fetchall()}

def save_status(data):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM status")
        conn.executemany(
            "INSERT INTO status(site, down_since) VALUES (?, ?)",
            [(k, v.get("down_since")) for k, v in data.items()],
        )
        conn.commit()

def check_sites():
    sites = load_sites()
    if not sites:
        return
    status = load_status()
    now = datetime.datetime.utcnow()

    def fetch(site):
        try:
            r = requests.get(site, timeout=REQUEST_TIMEOUT)
            return site, r.status_code
        except Exception:
            return site, None

    with ThreadPoolExecutor(max_workers=min(10, len(sites))) as executor:
        try:
            results = list(executor.map(fetch, sites))
        except RuntimeError:
            return

    for site, code in results:
        if code == 200:
            log_event({"type": "site_check", "site": site, "status": "up", "available": 1})
            if site in status and status[site]["down_since"]:
                send_alert(f"✅ {site} is back online", disable_web_page_preview=True)
            status[site] = {"down_since": None}
        else:
            if site not in status or status[site]["down_since"] is None:
                status[site] = {"down_since": now.isoformat()}
            else:
                delta = now - datetime.datetime.fromisoformat(status[site]["down_since"])
                minutes = int(delta.total_seconds() // 60)
                if minutes >= 3 and (minutes - 3) % 60 == 0:
                    hours = minutes // 60
                    mins = minutes % 60
                    log_event({
                        "type": "site_check",
                        "site": site,
                        "status": "down",
                        "available": 0,
                        "duration_min": minutes
                    })
                    if hours:
                        send_alert(
                            f"❌ {site} is down for {hours}h {mins}m",
                            disable_web_page_preview=True,
                        )
                    else:
                        send_alert(
                            f"❌ {site} is down for {mins}m",
                            disable_web_page_preview=True,
                        )

    save_status(status)

def check_ssl():
    sites = load_sites()
    results = ["🔐 SSL certificates lifetime:"]
    for site in sites:
        hostname = urlparse(site).hostname
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.settimeout(5)
                s.connect((hostname, 443))
                cert = s.getpeercert()
                expires = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                days_left = (expires - datetime.datetime.utcnow()).days
                status_icon = "⚠️" if days_left <= 7 else "✅"
                results.append(f"{status_icon} {hostname} — {days_left} days")
                log_event(
                    {
                        "type": "ssl_check",
                        "site": hostname,
                        "status": "valid",
                        "days_left": days_left,
                    }
                )
        except:
            results.append(f"❌ {hostname}: SSL certificate not available")
            log_event({"type": "ssl_check", "site": hostname, "status": "error"})
    return "\n".join(results)

def daily_ssl_loop():
    while True:
        try:
            now = datetime.datetime.utcnow()
            target = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if now >= target:
                target += datetime.timedelta(days=1)
            sleep_seconds = (target - now).total_seconds()
            time.sleep(sleep_seconds)

            result = check_ssl()
            alerts = [line for line in result.splitlines() if line.startswith("⚠️")]
            if alerts:
                send_alert(
                    "⚠️ Sites with expiring SSL certificates:\n" + "\n".join(alerts),
                    disable_web_page_preview=True,
                )
        except Exception as e:
            print(f"[daily_ssl_loop error] {e}")
