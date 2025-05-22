FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN test -f /app/status.json || echo '{}' > /app/status.json

CMD ["python", "/app/bot.py"]