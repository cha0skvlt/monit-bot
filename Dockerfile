FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]

HEALTHCHECK CMD python -c "import sqlite3, os; sqlite3.connect(os.getenv('DB_FILE','/app/db.sqlite')).execute('SELECT 1')"
