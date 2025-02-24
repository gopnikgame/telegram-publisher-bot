#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
TEMP_DIR=$(mktemp -d)
PROJECT_DIR="telegram-publisher-bot" # Имя директории, которая будет создана после клонирования

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

# Основной скрипт
log "GREEN" "🤖 Установка/обновление Telegram Publisher Bot"

# Проверяем root права
if [ "$EUID" -ne 0 ]; then
    log "RED" "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Устанавливаем зависимости (если их нет)
if ! command -v git &> /dev/null; then
    log "YELLOW" "⚠️ Git не установлен. Устанавливаем..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# Клонируем репозиторий во временную директорию
log "BLUE" "⬇️ Клонирование репозитория во временную директорию..."
git clone "$REPO_URL" "$TEMP_DIR/$PROJECT_DIR"

# Переходим во временную директорию
log "BLUE" "📂 Переход в директорию проекта..."
cd "$TEMP_DIR/$PROJECT_DIR"

# Проверяем наличие необходимых файлов
if [ ! -f "docker-compose.yml" ] && [ ! -f ".env.example" ]; then
    log "RED" "❌ Не найдены необходимые файлы проекта (docker-compose.yml или .env.example)"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Запускаем основной скрипт установки
log "BLUE" "🚀 Запуск основного скрипта установки..."
bash install_or_update_bot.sh

# Удаляем временную директорию после завершения
#log "BLUE" "🧹 Удаление временной директории..."
#rm -rf "$TEMP_DIR"

log "GREEN" "✅ Установка завершена!"

exit 0