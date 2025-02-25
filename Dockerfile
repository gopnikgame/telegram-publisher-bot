FROM python:3.9-slim-buster

WORKDIR /app

# Remove existing virtual environment (if any)
RUN rm -rf /usr/local/lib/python3.9/site-packages

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /opt/telegram-publisher-bot/logs

COPY . .

CMD ["python", "-m", "app"]