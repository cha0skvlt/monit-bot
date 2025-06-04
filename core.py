#!/usr/bin/env python3
import os, json, ssl, socket, datetime, requests, logging, time
from telegram import Bot
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SITES_FILE = os.getenv("SITES_FILE", "/app/sites.txt")
STATUS_FILE = os.getenv("STATUS_FILE", "/app/status.json")
LOG_FILE = os.getenv("LOG_FILE", "/app/logs/monitor.log")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(message)s")

def log_event(data: dict):
    """Append structured JSON event to log file."""
    data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    logging.info(json.dumps(data))

_bot = None


def _get_bot():
    global _bot
    if _bot is None:
        _bot = Bot(BOT_TOKEN)
    return _bot


def send_alert(msg, disable_web_page_preview=True):
    try:
        _get_bot().send_message(
            chat_id=CHAT_ID,
            text=msg,
            disable_web_page_preview=disable_web_page_preview,
        )
    except Exception:
        pass

def load_sites():
    if not os.path.exists(SITES_FILE):
        return []
    with open(SITES_FILE) as f:
        return [line.strip() for line in f if line.strip()]

def save_sites(sites):
    with open(SITES_FILE, "w") as f:
        for s in sites:
            f.write(s.strip() + "\n")

def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def check_sites():
    sites = load_sites()
    if not sites:
        return
    status = load_status()
    now = datetime.datetime.utcnow()

    def fetch(site):
        try:
            r = requests.get(site, timeout=10)
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
                if minutes == 5 or (minutes > 5 and minutes % 60 == 0):
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
                        send_alert(f"❌ {site} is down for {hours}h {mins}m", disable_web_page_preview=True)
                    else:
                        send_alert(f"❌ {site} is down for {mins}m", disable_web_page_preview=True)

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
                log_event({"type": "ssl_check", "site": hostname, "status": "valid", "days_left": days_left})
        except:
            results.append(f"❌ {hostname}: SSL certificate not available")
            log_event({"type": "ssl_check", "site": hostname, "status": "error"})
    return "\n".join(results)

def daily_ssl_loop():
    while True:
        now = datetime.datetime.utcnow()
        target = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        time.sleep(sleep_seconds)

        result = check_ssl()
        alerts = [line for line in result.splitlines() if line.startswith("⚠️")]
        if alerts:
            send_alert("⚠️ Sites with expiring SSL certificates:\n" + "\n".join(alerts), disable_web_page_preview=True)
