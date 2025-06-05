import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core
import requests
import threading

def test_save_and_load_sites(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    monkeypatch.setattr(core, "DB_FILE", str(db))
    core.init_db.done = False

    # initially file does not exist
    assert core.load_sites() == []

    data = ["https://example.com", "https://google.com"]
    core.save_sites(data)
    assert db.exists()

    loaded = core.load_sites()
    assert loaded == data


def test_check_sites_parallel(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    monkeypatch.setattr(core, "DB_FILE", str(db))
    core.init_db.done = False
    monkeypatch.setattr(core, "send_alert", lambda *a, **k: None)
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)

    core.save_sites(["https://ok.com", "https://bad.com"])

    class Resp:
        def __init__(self, code):
            self.status_code = code

    def fake_get(url, timeout=10):
        if "ok.com" in url:
            return Resp(200)
        raise requests.RequestException

    monkeypatch.setattr(core.requests, "get", fake_get)

    core.check_sites()

    status = core.load_status()
    assert status["https://ok.com"]["down_since"] is None
    assert status["https://bad.com"]["down_since"] is not None

def test_check_sites_alert_threshold(monkeypatch):
    site = "https://bad.com"
    monkeypatch.setattr(core, "load_sites", lambda: [site])
    fixed_now = core.datetime.datetime(2024, 1, 1, 0, 10, 0)
    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now
    monkeypatch.setattr(core.datetime, "datetime", FixedDT)
    status = {site: {"down_since": (fixed_now - core.datetime.timedelta(minutes=3)).isoformat()}}
    monkeypatch.setattr(core, "load_status", lambda: status.copy())
    saved = {}
    monkeypatch.setattr(core, "save_status", lambda d: saved.update(d))
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)
    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))
    def fake_get(url, timeout=10):
        raise requests.RequestException
    monkeypatch.setattr(core.requests, "get", fake_get)
    core.check_sites()
    assert alerts and "down for 3m" in alerts[0]
    assert saved[site]["down_since"] == status[site]["down_since"]


def test_check_sites_recovery(monkeypatch):
    site = "https://ok.com"
    monkeypatch.setattr(core, "load_sites", lambda: [site])
    fixed_now = core.datetime.datetime(2024, 1, 1, 0, 20, 0)
    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now
    monkeypatch.setattr(core.datetime, "datetime", FixedDT)
    status = {site: {"down_since": (fixed_now - core.datetime.timedelta(minutes=10)).isoformat()}}
    monkeypatch.setattr(core, "load_status", lambda: status.copy())
    saved = {}
    monkeypatch.setattr(core, "save_status", lambda d: saved.update(d))
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)
    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))
    class Resp:
        def __init__(self, code):
            self.status_code = code
    monkeypatch.setattr(core.requests, "get", lambda url, timeout=10: Resp(200))
    core.check_sites()
    assert alerts and alerts[0].startswith("✅")
    assert saved[site]["down_since"] is None


def test_check_sites_no_sites(monkeypatch):
    monkeypatch.setattr(core, "load_sites", lambda: [])
    monkeypatch.setattr(core, "load_status", lambda: {})

    monkeypatch.setattr(
        core,
        "save_status",
        lambda d: (_ for _ in ()).throw(AssertionError("should not save")),
    )

    monkeypatch.setattr(
        core,
        "save_status",
        lambda d: (_ for _ in ()).throw(AssertionError("should not save")),
    )

    core.check_sites()  # should not raise


def test_env_override_files(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_FILE", str(tmp_path / "db.sqlite"))
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "log.log"))
    import importlib
    import core as core_mod
    importlib.reload(core_mod)
    try:
        assert core_mod.DB_FILE == str(tmp_path / "db.sqlite")
        assert core_mod.LOG_FILE == str(tmp_path / "log.log")
    finally:
        monkeypatch.delenv("DB_FILE", raising=False)
        monkeypatch.delenv("LOG_FILE", raising=False)
        importlib.reload(core_mod)


def test_env_defaults(monkeypatch):
    import importlib
    import core as core_mod
    monkeypatch.delenv("DB_FILE", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    monkeypatch.delenv("REQUEST_TIMEOUT", raising=False)
    importlib.reload(core_mod)
    try:
        assert core_mod.DB_FILE == "/app/db.sqlite"
        assert core_mod.LOG_FILE == "/app/logs/monitor.log"
        assert core_mod.REQUEST_TIMEOUT == 10
    finally:
        importlib.reload(core_mod)


def test_db_file_directory(tmp_path, monkeypatch):
    import importlib
    d = tmp_path / "data"
    d.mkdir()
    monkeypatch.setenv("DB_FILE", str(d))
    import core as core_mod
    importlib.reload(core_mod)
    try:
        core_mod.init_db()
        assert core_mod.DB_FILE == str(d / "db.sqlite")
        assert (d / "db.sqlite").exists()
    finally:
        monkeypatch.delenv("DB_FILE", raising=False)
        importlib.reload(core_mod)


def test_request_timeout_usage(tmp_path, monkeypatch):
    db = tmp_path / "db.sqlite"
    monkeypatch.setattr(core, "DB_FILE", str(db))
    core.init_db.done = False
    monkeypatch.setattr(core, "send_alert", lambda *a, **k: None)
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)

    core.save_sites(["https://ok.com"])

    called = {}

    def fake_get(url, timeout=None):
        called["timeout"] = timeout
        class Resp:
            status_code = 200
        return Resp()

    monkeypatch.setattr(core.requests, "get", fake_get)
    monkeypatch.setattr(core, "REQUEST_TIMEOUT", 5)
    core.check_sites()
    assert called.get("timeout") == 5



def test_alert_after_adding_bad_site(tmp_path, monkeypatch):
    site = "https://bad.com"
    db = tmp_path / "db.sqlite"
    monkeypatch.setattr(core, "DB_FILE", str(db))
    core.init_db.done = False
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)

    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))

    def fake_get(url, timeout=10):
        raise requests.RequestException
    monkeypatch.setattr(core.requests, "get", fake_get)

    base = core.datetime.datetime(2024, 1, 1, 0, 0, 0)
    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls.current
    FixedDT.current = base
    monkeypatch.setattr(core.datetime, "datetime", FixedDT)

    core.save_sites([site])
    core.check_sites()
    assert not alerts

    FixedDT.current = base + core.datetime.timedelta(minutes=3)
    core.check_sites()
    assert alerts and "down for 3m" in alerts[0]


def test_hourly_reminder_after_downtime(tmp_path, monkeypatch):
    site = "https://bad.com"
    db = tmp_path / "db.sqlite"
    monkeypatch.setattr(core, "DB_FILE", str(db))
    core.init_db.done = False
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)

    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))

    def fake_get(url, timeout=10):
        raise requests.RequestException
    monkeypatch.setattr(core.requests, "get", fake_get)

    base = core.datetime.datetime(2024, 1, 1, 0, 0, 0)
    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls.current
    FixedDT.current = base
    monkeypatch.setattr(core.datetime, "datetime", FixedDT)

    core.save_sites([site])
    core.check_sites()

    FixedDT.current = base + core.datetime.timedelta(minutes=3)
    core.check_sites()

    FixedDT.current = base + core.datetime.timedelta(minutes=63)
    core.check_sites()

    assert any("down for 1h 3m" in a for a in alerts)


def test_alert_with_partial_minutes(monkeypatch):
    site = "https://bad.com"
    monkeypatch.setattr(core, "load_sites", lambda: [site])
    now = core.datetime.datetime(2024, 1, 1, 1, 0, 0)

    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return now

    monkeypatch.setattr(core.datetime, "datetime", FixedDT)
    status = {
        site: {
            "down_since": (
                now - core.datetime.timedelta(minutes=3, seconds=10)
            ).isoformat()
        }
    }
    monkeypatch.setattr(core, "load_status", lambda: status.copy())
    saved = {}
    monkeypatch.setattr(core, "save_status", lambda d: saved.update(d))
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)
    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))

    def fake_get(url, timeout=10):
        raise requests.RequestException

    monkeypatch.setattr(core.requests, "get", fake_get)
    core.check_sites()
    assert alerts and "down for 3m" in alerts[0]


def test_get_bot_single_instance(monkeypatch):
    created = []

    class FakeBot:
        def __init__(self, token):
            created.append(token)

    monkeypatch.setattr(core, "Bot", FakeBot)
    monkeypatch.setattr(core, "BOT_TOKEN", "T")
    core._bot = None
    core._bot_lock = threading.Lock()

    objs = []

    def worker():
        objs.append(core._get_bot())

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start(); t2.start(); t1.join(); t2.join()

    assert objs[0] is objs[1]
    assert len(created) == 1
