import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import requests

import bot
import core
from types import SimpleNamespace

class DummyChat:
    def __init__(self):
        self.actions = []
    def send_action(self, action):
        self.actions.append(action)

class DummyMessage:
    def __init__(self):
        self.chat = DummyChat()
        self.texts = []
    def reply_text(self, text, disable_web_page_preview=True):
        self.texts.append(text)

class DummyUpdate:
    def __init__(self):
        self.message = DummyMessage()

class DummyContext(SimpleNamespace):
    pass

def _call(func, args=None):
    upd = DummyUpdate()
    ctx = DummyContext(args=args or [])
    func(upd, ctx)
    return upd.message.texts[0]

def test_bot_command_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "DB_FILE", str(tmp_path / "db.sqlite"))
    core.init_db.done = False
    monkeypatch.setattr(core, "LOG_FILE", str(tmp_path / "log.log"))
    monkeypatch.setattr(core, "log_event", lambda *a, **k: None)

    alerts = []
    monkeypatch.setattr(core, "send_alert", lambda msg, **k: alerts.append(msg))
    monkeypatch.setattr(bot, "check_ssl", lambda: "SSL OK")

    monkeypatch.setattr(core, "site_is_up", lambda url: True)

    text = _call(bot.cmd_add, ["https://x.com"])
    assert "Added" in text

    text = _call(bot.cmd_list)
    assert "https://x.com" in text

    text = _call(bot.cmd_status)
    assert "OK" in text

    text = _call(bot.cmd_ssl_check)
    assert text == "SSL OK"

    monkeypatch.setattr(core, "site_is_up", lambda url: False)

    base = core.datetime.datetime(2024, 1, 1, 0, 0, 0)

    class FixedDT(core.datetime.datetime):
        @classmethod
        def utcnow(cls):
            return cls.current

    monkeypatch.setattr(core.datetime, "datetime", FixedDT)

    FixedDT.current = base
    core.check_sites()
    FixedDT.current = base + core.datetime.timedelta(minutes=3)
    core.check_sites()
    assert any("down for 3m" in a for a in alerts)

    monkeypatch.setattr(core, "site_is_up", lambda url: True)
    FixedDT.current = base + core.datetime.timedelta(minutes=4)
    core.check_sites()
    assert any(a.startswith("✅") for a in alerts)

    text = _call(bot.cmd_remove, ["https://x.com"])
    assert "Removed" in text
    text = _call(bot.cmd_list)
    assert "https://x.com" not in text

    text = _call(bot.cmd_start)
    assert "3" in text
