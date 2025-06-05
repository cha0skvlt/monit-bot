import os
import subprocess
from pathlib import Path

def test_start_sh_creates_status(tmp_path):
    db = tmp_path / "db.sqlite"
    script = Path(__file__).resolve().parents[1] / "start.sh"
    env = os.environ.copy()
    env["DB_FILE"] = str(db)
    env["SKIP_BOT"] = "1"
    subprocess.run(["sh", str(script)], check=True, env=env)
    assert db.exists()
    import sqlite3
    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"sites", "status", "logs"} <= tables

