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
    status = load_status()
    now = datetime.datetime.utcnow()

    for site in sites:
        try:
            r = requests.get(site, timeout=10)
            if r.status_code == 200:
                if site in status and status[site]["down_since"]:
                    send_alert(f"✅ {site} восстановлен")
                status[site] = {"down_since": None}
            else:
                raise Exception(f"Status {r.status_code}")
        except:
            if site not in status or status[site]["down_since"] is None:
                # первое падение — установить таймер
                status[site] = {"down_since": now.isoformat()}
            else:
                # уже падал — считаем время
                down_time = datetime.datetime.fromisoformat(status[site]["down_since"])
                delta = now - down_time
                minutes = int(delta.total_seconds() // 60)

                if minutes >= 5 and minutes % 10 == 0:
                    send_alert(f"❌ {site} недоступен {minutes} минут")

    save_status(status)

def check_ssl():
    sites = load_sites()
    results = ["🔐 SSL-сертификаты:"]
    for site in sites:
        hostname = urlparse(site).hostname
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.settimeout(5)
                s.connect((hostname, 443))
                cert = s.getpeercert()
                expires = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expires - datetime.datetime.utcnow()).days
                date_str = expires.strftime('%Y-%m-%d')
                results.append(f"- {hostname}: {days_left} дней до окончания ({date_str})")
        except:
            results.append(f"- {hostname}: ❌ сертификат не получен")
    return "\n".join(results)