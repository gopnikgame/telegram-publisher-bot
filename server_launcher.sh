#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
PROJECT_DIR="telegram-publisher-bot"
INSTALL_DIR="/opt/$PROJECT_DIR" # Постоянная директория для установки
LOG_FILE="/var/log/telegram-publisher-bot.log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    local level=$1
    local message=$2
    echo -e "${!level}${message}${NC}" | tee -a "$LOG_FILE"
}

# Проверка зависимостей
log "BLUE" "🔍 Проверка зависимостей..."
if ! command -v git &> /dev/null || ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null || ! command -v nano &> /dev/null; then
    log "YELLOW" "⚠️ Установка необходимых пакетов..."
    apt-get update
    apt-get install -y git docker.io docker-compose nano
fi

# Проверка существования директории установки
if [ -d "$INSTALL_DIR" ]; then
    log "BLUE" "🚀 Директория установки существует: $INSTALL_DIR"
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    # Добавляем права на выполнение скрипта manage_bot.sh
    chmod +x scripts/manage_bot.sh
    # Запускаем скрипт manage_bot.sh
    log "BLUE" "🚀 Запуск основного скрипта установки..."
    ./scripts/manage_bot.sh
else
    log "BLUE" "⬇️ Клонирование репозитория..."
    # Создаем временную директорию
    TEMP_DIR=$(mktemp -d)
    # Переходим во временную директорию
    cd "$TEMP_DIR"
    # Клонируем репозиторий
    git clone "$REPO_URL" "$PROJECT_DIR"
    # Переходим в директорию проекта
    cd "$PROJECT_DIR"
    # Создаем директорию установки, если она не существует
    mkdir -p "$INSTALL_DIR"
    # Копируем файлы в директорию установки
    log "BLUE" "📦 Копирование файлов в директорию установки..."
    cp -r . "$INSTALL_DIR"
    # Переходим в директорию установки
    cd "$INSTALL_DIR"
    # Добавляем права на выполнение скрипта manage_bot.sh
    chmod +x scripts/manage_bot.sh
    # Запускаем скрипт manage_bot.sh
    log "BLUE" "🚀 Запуск основного скрипта установки..."
    ./scripts/manage_bot.sh
    # Удаляем временную директорию
    rm -rf "$TEMP_DIR"
fi

log "GREEN" "✅ Установка/обновление завершено"