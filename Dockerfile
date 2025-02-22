FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов приложения
COPY app/ ./app/

# Создание директории для логов
RUN mkdir -p logs

# Запуск бота
CMD ["python", "-m", "app.bot"]