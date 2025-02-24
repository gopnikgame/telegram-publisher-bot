FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем пользователя для запуска приложения
ARG DOCKER_UID=1000
ARG DOCKER_GID=1000
RUN groupadd -g $DOCKER_GID appuser && \
    useradd -m -u $DOCKER_UID -g $DOCKER_GID appuser

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для логов
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Копируем код приложения (без .env)
COPY --chown=appuser:appuser app app/
COPY --chown=appuser:appuser requirements.txt .

# Переключаемся на пользователя appuser
USER appuser

# Проверяем наличие переменных окружения при запуске
CMD if [ -f /app/.env ]; then \
        echo "Checking .env file..."; \
        if grep -q "^BOT_TOKEN=" /app/.env; then \
            echo "Starting bot..."; \
            python -m app; \
        else \
            echo "ERROR: BOT_TOKEN not found in .env file"; \
            exit 1; \
        fi; \
    else \
        echo "ERROR: .env file not found"; \
        exit 1; \
    fi