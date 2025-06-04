import os
import subprocess
from pathlib import Path

def test_start_sh_creates_status(tmp_path):
    status = tmp_path / "status.json"
    script = Path(__file__).resolve().parents[1] / "start.sh"
    env = os.environ.copy()
    env["STATUS_FILE"] = str(status)
    env["SKIP_BOT"] = "1"
    subprocess.run(["sh", str(script)], check=True, env=env)
    assert status.exists()
    assert status.read_text().strip() == "{}"

