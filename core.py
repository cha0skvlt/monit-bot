#!/usr/bin/env python3

import datetime
import json
import logging
from logging import handlers
import os
import socket
import ssl
import re
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
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = os.getenv("LOG_FILE", "/app/logs/monitor.log")
OWNER_ID = os.getenv("OWNER_ID")
ADMIN_IDS = [s for s in os.getenv("ADMIN_IDS", "").split(",") if s]

DB_FILE = os.getenv("DB_FILE", "/app/db.sqlite")
# Treat a directory path or a new path without extension as a directory
if os.path.isdir(DB_FILE) or (
    not os.path.splitext(DB_FILE)[1] and not os.path.exists(DB_FILE)
):
    DB_FILE = os.path.join(DB_FILE, "db.sqlite")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

LEGACY_SITES_FILE = Path("/app/sites.txt")
LEGACY_STATUS_FILE = Path("/app/status.json")

URL_RE = re.compile(
    r"^https?://(?:[A-Za-z0-9-]+\.)+[A-Za-z0-9-]+(?:[:/].*)?$"
)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=3
)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[handler])


def init_db():
    """Create database and migrate data on first run."""
    if getattr(init_db, "done", False):
        return
    dir_name = os.path.dirname(DB_FILE) or "."
    os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS sites (url TEXT PRIMARY KEY)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS status (site TEXT PRIMARY KEY, down_since TEXT)"
    )
    cur.execute("CREATE TABLE IF NOT EXISTS logs (data TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY)")
    if ADMIN_IDS or OWNER_ID:
        existing = {str(r[0]) for r in cur.execute("SELECT id FROM admins")}
        for a in list(ADMIN_IDS) + ([OWNER_ID] if OWNER_ID else []):
            if a and a not in existing:
                cur.execute("INSERT INTO admins(id) VALUES (?)", (int(a),))
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


def send_alert(msg, disable_web_page_preview=True, chat_id=None):
    target_id = chat_id or CHAT_ID
    if not target_id:
        print("[send_alert] CHAT_ID not set")
        return
    try:
        _get_bot().send_message(
            chat_id=target_id,
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

def load_admins():
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id FROM admins")
        return [str(r[0]) for r in cur.fetchall()]

def add_admin(admin_id: str):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR IGNORE INTO admins(id) VALUES (?)", (int(admin_id),))
        conn.commit()

def remove_admin(admin_id: str):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM admins WHERE id=?", (int(admin_id),))
        conn.commit()

def is_valid_url(url: str) -> bool:
    if not url or not URL_RE.match(url):
        return False
    p = urlparse(url)
    return p.scheme in {"http", "https"} and bool(p.hostname)

def site_is_up(url: str) -> bool:
    headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
    try:
        r = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, headers=headers)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    for i in range(3):
        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, headers=headers)
            if r.status_code == 200:
                return True
            break
        except Exception:
            if i < 2:
                time.sleep(1)
            else:
                pass
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except Exception:
        return False
    for family, socktype, proto, canonname, sockaddr in infos:
        try:
            with socket.create_connection(sockaddr, REQUEST_TIMEOUT) as conn:
                if parsed.scheme == "https":
                    ctx = ssl.create_default_context()
                    with ctx.wrap_socket(conn, server_hostname=host) as s:
                        req = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                        s.sendall(req.encode())
                        data = s.recv(12)
                else:
                    req = f"HEAD {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                    conn.sendall(req.encode())
                    data = conn.recv(12)
            if b"200" in data.split(b"\r\n")[0]:
                return True
        except Exception:
            continue
    return False


def check_sites():
    sites = load_sites()
    if not sites:
        return
    status = load_status()
    now = datetime.datetime.utcnow()

    def fetch(site):
        try:
            return site, site_is_up(site)
        except Exception as e:
            log_event({"type": "site_check_error", "site": site, "error": str(e)})
            return site, False

    with ThreadPoolExecutor(max_workers=min(10, len(sites))) as executor:
        try:
            results = list(executor.map(fetch, sites))
        except RuntimeError:
            return

    for site, ok in results:
        if ok:
            log_event({"type": "site_check", "site": site, "status": "up", "available": 1})
            prev = status.get(site)
            if prev and prev.get("down_since"):
                send_alert(f"✅ {site} is back online", disable_web_page_preview=True)
                prev["down_since"] = None
            else:
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
                if days_left <= 7:
                    log_event({
                        "type": "ssl_alert",
                        "site": hostname,
                        "days_left": days_left,
                    })
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

init_db()

