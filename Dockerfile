FROM python:3.9-slim-buster

WORKDIR /app

# Install pip
RUN apt-get update && apt-get install -y python3-pip

# Remove existing virtual environment (if any)
RUN rm -rf /usr/local/lib/python3.9/site-packages

COPY requirements.txt .
# Явно указываем версию при установке
RUN pip install --no-cache-dir python-telegram-bot==20.0 -r requirements.txt

# Create logs directory
RUN mkdir -p /opt/telegram-publisher-bot/logs

COPY . .

CMD ["python", "-m", "app"]