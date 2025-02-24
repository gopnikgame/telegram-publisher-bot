#!/bin/bash

# Проверяем наличие и права на директории
echo "Checking directory permissions..."
ls -la /app
ls -la /app/logs

# Проверяем, что можем писать в директорию logs
if ! touch /app/logs/test.log 2>/dev/null; then
    echo "ERROR: Cannot write to /app/logs directory"
    exit 1
fi
rm -f /app/logs/test.log

# Проверяем наличие и содержимое .env файла
if [ ! -f /app/.env ]; then
    echo "ERROR: .env file not found"
    exit 1
fi

# Проверяем права на .env файл
if [ ! -r /app/.env ]; then
    echo "ERROR: Cannot read .env file"
    ls -la /app/.env
    exit 1
fi

# Экспортируем переменные из .env в окружение
set -a
source /app/.env
set +a

# Запускаем бота
exec python -m app