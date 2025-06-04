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
