tasks:
  - id: sec-url-validation
    title: "Валидация URL при добавлении сайта"
    description: >
      При добавлении сайта через /add необходимо проверять, что введённый URL валиден.
      Сейчас бот может принять произвольный текст, что приведёт к ошибке при проверке.
    tags: [security, validation, bot]
    priority: medium

  - id: sec-exception-handling
    title: "Обработка исключений в check_sites и check_ssl"
    description: >
      Обернуть вызовы requests и ssl в try/except, чтобы бот не падал при ошибке сети или недоступности.
    tags: [stability, core]
    priority: high

  - id: sec-admin-restriction
    title: "Ограничение доступа к командам по Telegram ID"
    description: >
      Добавить список разрешённых Telegram ID в .env. Проверять ID в каждой команде. 
      Только администраторы из списка могут вызывать команды.
    tags: [security, access-control]
    priority: high

  - id: feature-admin-dynamic
    title: "Команды /add_admin и /rm_admin для управления доступом"
    description: >
      Позволить добавлять новых админов командой /add_admin <id>, и удалять их через /rm_admin <id>.
      Только основной владелец (из .env) может добавлять и удалять админов. Админы не могут добавлять других админов.
    tags: [bot, access-control]
    priority: high

  - id: cmd-remove-rename
    title: "Переименовать команду /remove в /rem"
    description: >
      Изменить название команды удаления сайта на /rem для краткости и удобства.
    tags: [UX, bot]
    priority: low

  - id: log-rotation
    title: "Добавить ротацию логов"
    description: >
      Использовать logging.handlers.RotatingFileHandler вместо basicConfig, чтобы избежать переполнения файла логов.
    tags: [logging]
    priority: medium

  - id: help-localization
    title: "Добавить локализацию справки"
    description: >
      Команда /help должна выдавать справку на языке пользователя (русский/английский) через `user.language_code`.
    tags: [UX, localization]
    priority: low

  - id: docker-healthcheck
    title: "Добавить HEALTHCHECK в Dockerfile"
    description: >
      Добавить Docker HEALTHCHECK, проверяющий работу бота или доступность SQLite, для мониторинга контейнера.
    tags: [docker, devops]
    priority: low

  - id: cmd-ssl-on-demand
    title: "Проверка SSL по команде /checkssl"
    description: >
      Убедиться, что SSL-проверка по /checkssl запускается в отдельном потоке и не блокирует Telegram-бота.
    tags: [ssl, async]
    priority: medium

  - id: tests-coverage
    title: "Расширить тесты на невалидные вводы и сбои"
    description: >
      Добавить тесты для невалидных URL, таймаутов, падения SSL, 403/500 HTTP-ответов.
    tags: [tests, robustness]
    priority: high
