import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core
import requests

def test_save_and_load_sites(tmp_path, monkeypatch):
    tmp_file = tmp_path / "sites.txt"
    monkeypatch.setattr(core, "SITES_FILE", str(tmp_file))

    # initially file does not exist
    assert core.load_sites() == []

    data = ["https://example.com", "https://google.com"]
    core.save_sites(data)
    assert tmp_file.exists()

    loaded = core.load_sites()
    assert loaded == data


def test_check_sites_parallel(tmp_path, monkeypatch):
    sites_file = tmp_path / "sites.txt"
    status_file = tmp_path / "status.json"
    monkeypatch.setattr(core, "SITES_FILE", str(sites_file))
    monkeypatch.setattr(core, "STATUS_FILE", str(status_file))
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
    status = {site: {"down_since": (fixed_now - core.datetime.timedelta(minutes=5)).isoformat()}}
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
    assert alerts and "down for 5m" in alerts[0]
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


def test_env_override_files(tmp_path, monkeypatch):
    monkeypatch.setenv("SITES_FILE", str(tmp_path / "s.txt"))
    monkeypatch.setenv("STATUS_FILE", str(tmp_path / "st.json"))
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "log.log"))
    import importlib
    import core as core_mod
    importlib.reload(core_mod)
    try:
        assert core_mod.SITES_FILE == str(tmp_path / "s.txt")
        assert core_mod.STATUS_FILE == str(tmp_path / "st.json")
        assert core_mod.LOG_FILE == str(tmp_path / "log.log")
    finally:
        monkeypatch.delenv("SITES_FILE", raising=False)
        monkeypatch.delenv("STATUS_FILE", raising=False)
        monkeypatch.delenv("LOG_FILE", raising=False)
        importlib.reload(core_mod)


def test_env_defaults(monkeypatch):
    import importlib
    import core as core_mod
    monkeypatch.delenv("SITES_FILE", raising=False)
    monkeypatch.delenv("STATUS_FILE", raising=False)
    monkeypatch.delenv("LOG_FILE", raising=False)
    importlib.reload(core_mod)
    try:
        assert core_mod.SITES_FILE == "/app/sites.txt"
        assert core_mod.STATUS_FILE == "/app/status.json"
        assert core_mod.LOG_FILE == "/app/logs/monitor.log"
    finally:
        importlib.reload(core_mod)


def test_log_dir_autocreate(tmp_path, monkeypatch):
    log_dir = tmp_path / "sub" / "dir"
    log_file = log_dir / "log.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    import importlib, logging
    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)
    import core as core_mod
    importlib.reload(core_mod)
    try:
        assert log_file.exists()
    finally:
        monkeypatch.delenv("LOG_FILE", raising=False)
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
        importlib.reload(core_mod)


