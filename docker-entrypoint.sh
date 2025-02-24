#!/bin/bash

# Проверяем наличие и содержимое .env файла
if [ ! -f /app/.env ]; then
    echo "ERROR: .env file not found"
    exit 1
fi

# Проверяем права на .env файл
if [ ! -r /app/.env ]; then
    echo "ERROR: Cannot read .env file"
    exit 1
fi

# Проверяем содержимое .env файла
if ! grep -q "^BOT_TOKEN=" /app/.env; then
    echo "ERROR: BOT_TOKEN not found in .env file"
    exit 1
fi

BOT_TOKEN=$(grep "^BOT_TOKEN=" /app/.env | cut -d'=' -f2-)
if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: BOT_TOKEN is empty in .env file"
    exit 1
fi

# Экспортируем переменные из .env
export $(cat /app/.env | grep -v '^#' | xargs)

# Запускаем бота
exec python -m app