import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core

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


def test_send_alert_disable_preview(monkeypatch):
    monkeypatch.setattr(core, "BOT_TOKEN", "TEST")
    monkeypatch.setattr(core, "CHAT_ID", "1")

    captured = {}

    def fake_post(url, data=None, timeout=5):
        captured['url'] = url
        captured['data'] = data
        captured['timeout'] = timeout
        class Resp:
            pass
        return Resp()

    monkeypatch.setattr(core.requests, "post", fake_post)
    core.send_alert("hello")

    assert captured['data']["disable_web_page_preview"] is True
