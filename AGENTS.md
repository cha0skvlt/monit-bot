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
