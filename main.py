import requests, json, ssl, socket, datetime, os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATUS_FILE = "/app/status.json"
SITES_FILE = "/app/sites.txt"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        pass  # не ломаем поток

def load_sites():
    with open(SITES_FILE) as f:
        return [line.strip() for line in f if line.strip()]

def load_status():
    if os.path.exists(STATUS_FILE):
        return json.load(open(STATUS_FILE))
    return {}

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def check_sites():
    sites = load_sites()
    status = load_status()
    now = datetime.datetime.utcnow().isoformat()

    for site in sites:
        try:
            r = requests.get(site, timeout=10)
            if r.status_code == 200:
                if site in status and status[site]["down_since"]:
                    send_alert(f"✅ {site} восстановлен")
                    status[site]["down_since"] = None
            else:
                raise Exception(f"Status {r.status_code}")
        except:
            if site not in status:
                status[site] = {"down_since": now}
            elif not status[site]["down_since"]:
                status[site]["down_since"] = now
            else:
                down_time = datetime.datetime.fromisoformat(status[site]["down_since"])
                delta = datetime.datetime.utcnow() - down_time
                if delta.total_seconds() > 300:
                    send_alert(f"❌ {site} недоступен >5 минут")
                    status[site]["down_since"] = None
    save_status(status)

def check_ssl():
    sites = load_sites()
    for site in sites:
        hostname = urlparse(site).hostname
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.settimeout(5)
                s.connect((hostname, 443))
                cert = s.getpeercert()
                expires = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                delta = (expires - datetime.datetime.utcnow()).days
                if delta < 7:
                    send_alert(f"⚠️ SSL {hostname} истекает через {delta} дней")
        except:
            pass
