#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
TEMP_DIR=$(mktemp -d)
PROJECT_DIR="telegram-publisher-bot"
INSTALL_DIR="/opt/$PROJECT_DIR" # Постоянная директория для установки
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_TIME="2025-02-24 21:08:19" # Текущее время в UTC

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
    echo -e "${!level}${message}${NC}"
}

# Функция очистки при выходе
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        log "BLUE" "🧹 Очистка временных файлов..."
        rm -rf "$TEMP_DIR"
    fi
}

# Функция для проверки и установки зависимостей
install_dependencies() {
    log "BLUE" "🔍 Проверка зависимостей..."
    
    local packages=("git" "docker.io" "docker-compose" "nano")
    local missing_packages=()

    for pkg in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $pkg"; then
            missing_packages+=("$pkg")
        fi
    done

    if [ ${#missing_packages[@]} -ne 0 ]; then
        log "YELLOW" "⚠️ Установка необходимых пакетов..."
        apt-get update
        apt-get install -y "${missing_packages[@]}"
    fi
}

# Регистрируем функцию очистки
trap cleanup EXIT

# Основной скрипт
log "GREEN" "🤖 Установка/обновление Telegram Publisher Bot"

# Проверяем root права
if [ "$EUID" -ne 0 ]; then
    log "RED" "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Устанавливаем зависимости
install_dependencies

# Создаем директорию для установки
if [ ! -d "$INSTALL_DIR" ]; then
    log "BLUE" "📂 Создание директории установки..."
    mkdir -p "$INSTALL_DIR"
fi

# Клонируем репозиторий во временную директорию
log "BLUE" "⬇️ Клонирование репозитория..."
if ! git clone "$REPO_URL" "$TEMP_DIR/$PROJECT_DIR"; then
    log "RED" "❌ Ошибка при клонировании репозитория"
    exit 1
fi

# Переходим во временную директорию
cd "$TEMP_DIR/$PROJECT_DIR"

# Проверяем наличие необходимых файлов
if [ ! -f "docker/docker-compose.yml" ] || [ ! -f "scripts/install_or_update_bot.sh" ]; then
    log "RED" "❌ Не найдены необходимые файлы проекта"
    exit 1
fi

# Копируем файлы в директорию установки
log "BLUE" "📦 Копирование файлов в директорию установки..."
rsync -a --delete ./ "$INSTALL_DIR/"

# Переходим в директорию установки
cd "$INSTALL_DIR"

# Устанавливаем переменные окружения
export CREATED_BY="$CURRENT_USER"
export CREATED_AT="$CURRENT_TIME"

# Устанавливаем права
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# Запускаем основной скрипт установки
log "BLUE" "🚀 Запуск основного скрипта установки..."
if [ -x "./scripts/install_or_update_bot.sh" ]; then
    ./scripts/install_or_update_bot.sh
else
    chmod +x "./scripts/install_or_update_bot.sh"
    ./scripts/install_or_update_bot.sh
fi

log "GREEN" "✅ Установка завершена!"
log "BLUE" "📍 Бот установлен в директорию: $INSTALL_DIR"

exit 0