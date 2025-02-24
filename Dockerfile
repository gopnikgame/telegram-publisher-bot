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

# Создаем директорию для логов и настраиваем права
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs  # Даем полные права на директорию logs

# Копируем код приложения (без .env)
COPY --chown=appuser:appuser app app/
COPY --chown=appuser:appuser requirements.txt .

# Добавляем скрипт для проверки и запуска
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Переключаемся на пользователя appuser
USER appuser

# Проверяем рабочую директорию и права
RUN pwd && ls -la && ls -la /app/logs

ENTRYPOINT ["/app/docker-entrypoint.sh"]