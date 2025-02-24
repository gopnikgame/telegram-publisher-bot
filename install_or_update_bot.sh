#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
TARGET_DIR="/opt/telegram-publisher-bot"
BACKUP_DIR="/opt/telegram-publisher-bot-backup"
DOCKER_UID=$(id -u)
DOCKER_GID=$(id -g)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

# Функция для проверки наличия команды
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log "RED" "❌ Ошибка: команда $1 не найдена"
        log "YELLOW" "📦 Установите необходимые зависимости:"
        log "YELLOW" "sudo apt-get update && sudo apt-get install -y $2"
        exit 1
    fi
}

# Функция для установки зависимостей
install_dependencies() {
    log "BLUE" "\n🔍 Проверка зависимостей..."
    
    local dependencies=(
        "git:git"
        "docker:docker.io"
        "docker-compose:docker-compose"
    )
    
    local missing_deps=()
    
    for dep in "${dependencies[@]}"; do
        IFS=":" read -r cmd pkg <<< "$dep"
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$pkg")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log "YELLOW" "⚠️ Отсутствуют необходимые зависимости"
        log "BLUE" "📦 Установка зависимостей..."
        sudo apt-get update
        sudo apt-get install -y "${missing_deps[@]}"
    fi
    
    log "GREEN" "✅ Все зависимости установлены"
}

# Функция для backup/restore .env файла
backup_restore_env() {
    local action=$1  # "backup" или "restore"
    local env_file="$TARGET_DIR/.env"
    local backup_file="$BACKUP_DIR/.env_$TIMESTAMP"
    
    if [ "$action" = "backup" ] && [ -f "$env_file" ]; then
        log "BLUE" "📑 Создание резервной копии .env файла..."
        mkdir -p "$BACKUP_DIR"
        cp "$env_file" "$backup_file"
        log "GREEN" "✅ Резервная копия .env создана: $backup_file"
    elif [ "$action" = "restore" ]; then
        if [ -f "$backup_file" ]; then
            log "BLUE" "📑 Восстановление .env файла..."
            cp "$backup_file" "$env_file"
            log "GREEN" "✅ .env файл восстановлен из: $backup_file"
        elif [ -f "$BACKUP_DIR/.env_"* ]; then
            # Если нет точного бэкапа, берем последний
            local latest_backup=$(ls -t "$BACKUP_DIR/.env_"* | head -n1)
            log "YELLOW" "⚠️ Восстановление из последнего бэкапа: $latest_backup"
            cp "$latest_backup" "$env_file"
            log "GREEN" "✅ .env файл восстановлен"
        fi
    fi
}

# Функция для настройки прав доступа
setup_permissions() {
    local target_dir="$1"
    log "BLUE" "🔧 Настройка прав доступа..."
    
    # Создаем директории
    mkdir -p "$target_dir/logs"
    
    # Устанавливаем права
    chmod -R 755 "$target_dir"
    chmod -R 777 "$target_dir/logs"
    chmod 600 "$target_dir/.env"
    
    # Устанавливаем владельца
    chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$target_dir"
    
    log "GREEN" "✅ Права доступа настроены"
}

# Функция для создания/редактирования .env файла
manage_env_file() {
    local env_file="$TARGET_DIR/.env"
    local env_example="$TARGET_DIR/.env.example"
    
    if [ ! -f "$env_file" ]; then
        if [ -f "$env_example" ]; then
            cp "$env_example" "$env_file"
            log "GREEN" "✅ Создан новый .env файл из примера"
        else
            log "RED" "❌ Файл .env.example не найден"
            return 1
        fi
    fi
    
    # Спрашиваем пользователя о редактировании
    read -r -p "Хотите отредактировать .env файл? [y/N] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        if command -v nano &> /dev/null; then
            nano "$env_file"
        else
            vi "$env_file"
        fi
    fi
}

# Функция для управления контейнером
manage_container() {
    local action=$1
    log "BLUE" "🐳 Управление контейнером..."
    
    cd "$TARGET_DIR"
    
    case $action in
        "restart")
            log "BLUE" "🔄 Перезапуск контейнера..."
            docker-compose down --remove-orphans
            docker-compose up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка контейнера..."
            docker-compose down --remove-orphans
            ;;
        "start")
            log "BLUE" "▶️ Запуск контейнера..."
            # Проверяем и удаляем старый контейнер если он существует
            if docker ps -a | grep -q "telegram-publisher-bot"; then
                log "YELLOW" "🔄 Удаление существующего контейнера..."
                docker rm -f telegram-publisher-bot
            fi
            # Устанавливаем переменные окружения для Docker
            export DOCKER_UID DOCKER_GID
            docker-compose up -d
            ;;
    esac
    
    # Проверяем результат
    if [ $? -eq 0 ]; then
        log "GREEN" "✅ Операция успешно выполнена"
    else
        log "RED" "❌ Ошибка при выполнении операции"
        return 1
    fi
}

# Функция для проверки статуса бота
check_bot_status() {
    log "BLUE" "🔍 Проверка статуса бота..."
    
    cd "$TARGET_DIR"
    
    if docker-compose ps | grep -q "telegram-publisher-bot"; then
        log "GREEN" "✅ Бот успешно работает"
        docker-compose logs --tail=10
    else
        log "RED" "❌ Бот не запущен"
        log "YELLOW" "Проверьте логи для деталей:"
        docker-compose logs --tail=20
    fi
}

# Функция для очистки старых логов и бэкапов
cleanup_old_files() {
    log "BLUE" "🧹 Очистка старых файлов..."
    
    # Удаляем старые бэкапы (оставляем последние 5)
    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t .env_* | tail -n +6 | xargs -r rm
    fi
    
    # Очищаем старые логи
    find "$TARGET_DIR/logs" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
    
    log "GREEN" "✅ Очистка завершена"
}

# Функция для обновления репозитория
update_repo() {
    log "BLUE" "🔄 Обновление репозитория..."
    
    # Создаем бэкап .env перед обновлением
    backup_restore_env "backup"
    
    if [ -d "$TARGET_DIR/.git" ]; then
        cd "$TARGET_DIR"
        git fetch
        git reset --hard origin/main
        log "GREEN" "✅ Репозиторий обновлен"
    else
        git clone "$REPO_URL" "$TARGET_DIR"
        log "GREEN" "✅ Репозиторий склонирован"
    fi
    
    # Восстанавливаем .env после обновления
    backup_restore_env "restore"
}

# Основной скрипт
log "GREEN" "🤖 Установка/обновление Telegram Publisher Bot"

# Проверяем root права
if [ "$EUID" -ne 0 ]; then 
    log "RED" "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверяем и устанавливаем зависимости
install_dependencies

# Создаем/обновляем целевую директорию
mkdir -p "$TARGET_DIR"

# Интерактивное меню
while true; do
    echo -e "\n📱 Telegram Publisher Bot - Меню установки\n"
    echo "1. 📝 Создать или редактировать .env файл"
    echo "2. 🚀 Собрать и запустить бота"
    echo "3. 📊 Показать логи (все)"
    echo "4. ❌ Показать логи ошибок"
    echo "5. 🔄 Перезапустить бота"
    echo "6. ⏹️ Остановить бота"
    echo "7. 📈 Статус бота"
    echo "8. ⬆️ Обновить из репозитория"
    echo "9. 🧹 Очистить старые логи и бэкапы"
    echo "10. 🚪 Выйти"
    
    read -r -p "Выберите действие (1-10): " choice
    
    case $choice in
        1)
            manage_env_file
            ;;
        2)
            update_repo
            setup_permissions "$TARGET_DIR"
            manage_container "start"
            check_bot_status
            ;;
        3)
            log "BLUE" "📜 Показ всех логов (Ctrl+C для выхода):"
            tail -f "$TARGET_DIR/logs/bot.log"
            ;;
        4)
            log "BLUE" "❌ Показ логов ошибок (Ctrl+C для выхода):"
            tail -f "$TARGET_DIR/logs/error.log"
            ;;
        5)
            cd "$TARGET_DIR"
            manage_container "restart"
            check_bot_status
            ;;
        6)
            cd "$TARGET_DIR"
            manage_container "stop"
            log "GREEN" "✅ Бот остановлен!"
            ;;
        7)
            check_bot_status
            ;;
        8)
            update_repo
            setup_permissions "$TARGET_DIR"
            log "GREEN" "✅ Репозиторий обновлен!"
            read -r -p "Хотите перезапустить бота? [y/N] " response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                manage_container "restart"
                check_bot_status
            fi
            ;;
        9)
            cleanup_old_files
            ;;
        10)
            log "GREEN" "👋 До свидания!"
            exit 0
            ;;
        *)
            log "RED" "❌ Неверный выбор. Попробуйте снова."
            ;;
    esac
done