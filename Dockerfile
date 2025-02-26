FROM python:3.13-buster

WORKDIR /app

# Set PATH
ENV PATH="/usr/local/bin:${PATH}"

# Install pip
RUN apt-get update && apt-get install -y python3-pip

# Check if pip is installed
RUN pip --version

# Remove existing virtual environment (if any)
RUN rm -rf /usr/local/lib/python3.9/site-packages

COPY requirements.txt .
# Явно указываем версию при установке
RUN python3 -m pip install --no-cache-dir python-telegram-bot==21.10 -r requirements.txt

# Create logs directory
RUN mkdir -p /opt/telegram-publisher-bot/logs

COPY . .

CMD ["python", "-m", "app"]