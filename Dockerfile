FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /opt/telegram-publisher-bot/logs

COPY . .

CMD ["python", "-m", "app"]