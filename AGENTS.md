# Codex Agent Guidelines

This project is a simple Telegram bot for website monitoring.
Follow these rules when modifying files:

## Coding Style
- Use Python 3.11 features with standard libraries only.
- Indent with 4 spaces and use double quotes for strings.
- Keep lines under 100 characters.

## Documentation
- Update `README.md` (English) and `docs/guide_ru.md` (Russian) when changing functionality.
- Document new environment variables in both files and in `.env.example`.

## Testing
- Add or update tests in `tests/` for any new behavior.
- Run the following commands before every commit and ensure they pass:
  ```bash
  pip install -q -r requirements.txt
  pytest -q
  ```

## Commits
- Keep commit messages concise: a short summary line and an optional bullet list of changes.
- 
# DEBUG: Проверка отправки уведомлений Telegram
# 1. В send_alert() игнорируются исключения — нужно логгировать:
#    except Exception as e:
#        print(f"[send_alert error] {e}")
#
# 2. Проверка, что CHAT_ID установлен:
#    if not CHAT_ID:
#        print("[send_alert] CHAT_ID not set")
#        return
#
# 3. Проверить переменные в .env:
#    CHAT_ID=123456789
#    BOT_TOKEN=...
#
# 4. Ручная проверка через:
#    from telegram import Bot
#    Bot(BOT_TOKEN).send_message(chat_id=CHAT_ID, text="test")
