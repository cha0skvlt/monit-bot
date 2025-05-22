import os, json, ssl, socket, datetime, requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SITES_FILE = "/app/sites.txt"
STATUS_FILE = "/app/status.json"

def send_alert(msg):
    """Отправка уведомления в Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        pass  # не ломаем поток

def load_sites():
    """Чтение списка сайтов из файла."""
    if not os.path.exists(SITES_FILE):
        return []
    with open(SITES_FILE) as f:
        return [line.strip() for line in f if line.strip()]

def save_sites(sites):
    """Сохранение списка сайтов в файл."""
    with open(SITES_FILE, "w") as f:
        for s in sites:
            f.write(s.strip() + "\n")

def load_status():
    """Чтение статуса сайтов (UP/DOWN) из файла."""
    if not os.path.exists(STATUS_FILE):
        return {}
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_status(data):
    """Сохранение статуса сайтов в файл."""
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def check_sites():
    """Проверка доступности сайтов."""
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
                status[site] = {"down_since": now.isoformat()}
            else:
                delta = now - datetime.datetime.fromisoformat(status[site]["down_since"])
                minutes = int(delta.total_seconds() // 60)
                if minutes >= 5 and minutes % 10 == 0:
                    send_alert(f"❌ {site} недоступен {minutes} минут")

    save_status(status)

def check_ssl():
    """Проверка SSL-сертификатов сайтов."""
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
