# Используем более новую версию Python
FROM python:3.11-slim

# Создаем нового пользователя для запуска бота
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только requirements.txt сначала для кэширования слоя
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта
COPY . .

# Создаем директорию для логов и устанавливаем права
RUN mkdir -p /app/logs && \
    chown -R botuser:botuser /app

# Переключаемся на пользователя botuser
USER botuser

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH=/app

# Запуск бота
CMD ["python", "-m", "app.bot"]