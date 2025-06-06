🔧 Codex Prompt: Полноценный Telegram-бот для мониторинга сайтов и SSL
Создай Telegram-бота на Python, который выполняет:

✅ Uptime Monitoring
Цель: следить за доступностью сайтов и оповещать при падениях/восстановлениях.

Проверка всех сайтов из базы раз в 3 минуты.

Если два раза подряд сайт не отвечает (то есть, не отвечает более 3 минут) — считается DOWN.

При этом бот:

сохраняет время первого падения (down_since)

отправляет оповещение в Telegram:
🔴 example.com DOWN (не работает с HH:MM UTC)

Если прошло более 1 часа с предыдущего оповещения и сайт всё ещё DOWN — бот повторяет оповещение.

Если сайт восстановлен (при следующей проверке снова ОК) — бот:

сбрасывает down_since

отправляет в Telegram:
🟢 example.com OK (восстановлен в HH:MM UTC)

🧪 Команда /status
По команде /status:

запускается немедленная проверка всех сайтов

выводится список в Telegram с текущим состоянием:

Копировать
Редактировать
✅ example.com — работает
🔴 badsite.net — не работает 2 дн. 4 ч. 18 мин.
если есть хотя бы один DOWN, отправляется отдельное оповещение.

🔐 SSL Monitoring
Цель: предупреждать, если SSL-сертификат скоро истечёт.

Ежедневно в 09:00 по Москве (Europe/Moscow) бот проверяет срок SSL у всех сайтов.

Если до окончания срока действия SSL осталось меньше 7 дней — бот:

сохраняет ssl_expires

отправляет в Telegram:
⚠️ example.com — SSL истекает через 5 дней (до DATE)

Повторяет оповещение раз в час, пока не будет получен новый сертификат.

🧪 Команда /ssl
По команде /ssl:

запускается немедленная SSL-проверка всех сайтов

Telegram-вывод в виде:

Копировать
Редактировать
✅ example.com — 58 дней до истечения
⚠️ badsite.net — 3 дня до истечения
⚙️ Управление URL-ами через Telegram
/list — список всех URL в базе

/add <URL> — добавляет сайт:

сначала проверяет его доступность

добавляет в базу

отправляет в Telegram:
✅ example.com добавлен — работает или
❌ example.com добавлен — недоступен

/remove <URL> — удаляет сайт из базы

💾 Хранение (SQLite)
Всё хранится в одном файле monitor.db. Структура:

Таблица urls
| url (TEXT, PRIMARY KEY) |

Таблица status
| url | down_since | last_alert_sent |

Таблица ssl
| url | ssl_expires (DATE) | ssl_last_alert_sent |

🛠️ Требования:
Python 3.x

Использовать библиотеки:

python-telegram-bot

apscheduler

requests, ssl, socket, sqlite3, datetime, dotenv

Переменные окружения в .env:

BOT_TOKEN=...

CHAT_ID=...

Важно:

Логика повторных оповещений должна учитывать last_alert_sent.

Убедись, что ошибки подключения/SSL корректно обрабатываются (try/except).

Учитывай таймзону Europe/Moscow при ежедневной проверке SSL.

Генерируй весь проект как единый Python-скрипт (или несколько при необходимости).


