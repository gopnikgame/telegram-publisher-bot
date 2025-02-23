FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Установка переменной окружения PYTHONPATH
ENV PYTHONPATH=/app

# Запуск бота
CMD ["python", "-m", "app.bot"]