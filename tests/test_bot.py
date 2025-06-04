import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import types
import core
import bot
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


def test_log_event(monkeypatch):
    logged = {}
    def fake_info(msg):
        logged["msg"] = msg
    monkeypatch.setattr(core.logging, "info", fake_info)
    core.log_event({"foo": "bar"})
    data = json.loads(logged["msg"])
    assert data["foo"] == "bar"
    assert "timestamp" in data


def test_send_alert(monkeypatch):
    calls = {}

    class FakeBot:
        def send_message(self, chat_id, text, disable_web_page_preview=True):
            calls["chat_id"] = chat_id
            calls["text"] = text

    monkeypatch.setattr(core, "Bot", lambda token: FakeBot())
    monkeypatch.setattr(core, "BOT_TOKEN", "TOKEN")
    monkeypatch.setattr(core, "CHAT_ID", "CID")
    core._bot = None  # reset cached bot
    core.send_alert("hi")
    assert calls["chat_id"] == "CID"
    assert calls["text"] == "hi"


def test_load_and_save_status(tmp_path, monkeypatch):
    f = tmp_path / "status.json"
    monkeypatch.setattr(core, "STATUS_FILE", str(f))
    data = {"site": {"down_since": None}}
    core.save_status(data)
    loaded = core.load_status()
    assert loaded == data


def test_check_ssl(monkeypatch):
    monkeypatch.setattr(core, "load_sites", lambda: ["https://ok.test", "https://bad.test"])
    def fake_log(*a, **k):
        pass
    monkeypatch.setattr(core, "log_event", fake_log)

    class FakeSocket:
        def __init__(self, fail=False):
            self.fail = fail
        def settimeout(self, t):
            pass
        def connect(self, addr):
            if self.fail:
                raise Exception("fail")
        def getpeercert(self):
            from datetime import datetime, timedelta
            expire = datetime.utcnow() + timedelta(days=5)
            return {"notAfter": expire.strftime("%b %d %H:%M:%S %Y GMT")}
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    class FakeCtx:
        def wrap_socket(self, sock, server_hostname=None):
            if "bad" in server_hostname:
                raise Exception("fail")
            return FakeSocket()
    monkeypatch.setattr(core.ssl, "create_default_context", lambda: FakeCtx())

    result = core.check_ssl()
    assert "ok.test" in result
    assert "bad.test" in result


def _call_cmd(func, ctx_args=None):
    update = DummyUpdate()
    ctx = DummyContext(args=ctx_args or [])
    func(update, ctx)
    return update


def test_with_typing_decorator(monkeypatch):
    called = {}
    def f(update, ctx):
        called["called"] = True
    wrapped = bot.with_typing(f)
    upd = DummyUpdate()
    ctx = DummyContext()
    wrapped(upd, ctx)
    assert called["called"]
    assert upd.message.chat.actions == [bot.ChatAction.TYPING]


def test_cmd_list(monkeypatch):
    monkeypatch.setattr(bot, "load_sites", lambda: ["a", "b"])
    upd = _call_cmd(bot.cmd_list)
    msg = upd.message.texts[0]
    assert "a" in msg and "b" in msg


def test_cmd_add(monkeypatch):
    sites = []
    monkeypatch.setattr(bot, "load_sites", lambda: sites)
    def fake_save(x):
        sites[:] = x
    monkeypatch.setattr(bot, "save_sites", fake_save)
    upd = _call_cmd(bot.cmd_add, ["x"])
    assert "Added" in upd.message.texts[0]
    assert "x" in sites


def test_cmd_remove(monkeypatch):
    sites = ["x"]
    status = {"x": {"down_since": None}}
    monkeypatch.setattr(bot, "load_sites", lambda: sites)
    monkeypatch.setattr(bot, "load_status", lambda: status)
    def fake_save_sites(x):
        sites[:] = x
    def fake_save_status(d):
        status.clear(); status.update(d)
    monkeypatch.setattr(bot, "save_sites", fake_save_sites)
    monkeypatch.setattr(bot, "save_status", fake_save_status)
    upd = _call_cmd(bot.cmd_remove, ["x"])
    assert "Removed" in upd.message.texts[0]
    assert sites == [] and status == {}


def test_cmd_status(monkeypatch):
    monkeypatch.setattr(bot, "check_sites", lambda: None)
    monkeypatch.setattr(bot, "load_sites", lambda: ["a"])
    monkeypatch.setattr(bot, "load_status", lambda: {"a": {"down_since": None}})
    upd = _call_cmd(bot.cmd_status)
    text = upd.message.texts[0]
    assert "a" in text and "OK" in text


def test_status_ignores_removed(monkeypatch):
    monkeypatch.setattr(bot, "check_sites", lambda: None)
    monkeypatch.setattr(bot, "load_sites", lambda: ["b"])
    monkeypatch.setattr(
        bot,
        "load_status",
        lambda: {"a": {"down_since": None}, "b": {"down_since": None}},
    )
    upd = _call_cmd(bot.cmd_status)
    text = upd.message.texts[0]
    assert "b" in text and "a —" not in text


def test_status_shows_down(monkeypatch):
    monkeypatch.setattr(bot, "check_sites", lambda: None)
    monkeypatch.setattr(bot, "load_sites", lambda: ["x"])
    monkeypatch.setattr(bot, "load_status", lambda: {"x": {"down_since": "2024-01-01T00:00:00"}})
    upd = _call_cmd(bot.cmd_status)
    text = upd.message.texts[0]
    assert "DOWN" in text and "x" in text


def test_status_ignores_removed(monkeypatch):
    monkeypatch.setattr(bot, "check_sites", lambda: None)
    monkeypatch.setattr(bot, "load_sites", lambda: ["b"])
    monkeypatch.setattr(bot, "load_status", lambda: {"a": {"down_since": None}, "b": {"down_since": None}})
    upd = _call_cmd(bot.cmd_status)
    text = upd.message.texts[0]
    assert "b" in text and "a —" not in text


def test_cmd_ssl_check(monkeypatch):
    monkeypatch.setattr(bot, "check_ssl", lambda: "SSL")
    upd = _call_cmd(bot.cmd_ssl_check)
    assert upd.message.texts[0] == "SSL"


def test_cmd_start():
    upd = _call_cmd(bot.cmd_start)
    text = upd.message.texts[0]
    assert "SSL auto-check" in text
    assert "/status" in text


def test_start_bot(monkeypatch):
    events = []

    class FakeUpdater:
        def __init__(self, token, use_context=True):
            self.dispatcher = SimpleNamespace(add_handler=lambda h: events.append(h))

        def start_polling(self):
            events.append("started")

    monkeypatch.setattr(bot, "Updater", FakeUpdater)
    monkeypatch.setattr(bot, "CommandHandler", lambda n, f: f"{n}:{f.__name__}")
    bot.start_bot()
    assert "started" in events
    assert any(e.startswith("status:") for e in events)

