import subprocess
from pathlib import Path


def test_telegram_test_sh(tmp_path):
    script = Path(__file__).resolve().parents[1] / "telegram_test.sh"
    env = {
        "BOT_TOKEN": "T",
        "CHAT_ID": "C",
        "SKIP_SEND": "1",
    }

    result = subprocess.run([
        "sh",
        str(script),
    ], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert "DRY RUN" in result.stdout


def test_telegram_test_sh_loads_env_file(tmp_path):
    script = Path(__file__).resolve().parents[1] / "telegram_test.sh"
    (tmp_path / ".env").write_text("BOT_TOKEN=T\nCHAT_ID=C\n")
    result = subprocess.run(
        ["sh", str(script)],
        env={"SKIP_SEND": "1"},
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(["sh", str(script)], env=env, capture_output=True, text=True)

    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
