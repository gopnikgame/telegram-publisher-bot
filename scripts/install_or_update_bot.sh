#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
PROJECT_DIR="telegram-publisher-bot"
INSTALL_DIR="/opt/$PROJECT_DIR" # Постоянная директория для установки
BACKUP_DIR="./backups"
LOG_DIR="./logs"
#BOT_NAME="telegram-publisher-bot" # Теперь BOT_NAME устанавливается в .env
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_TIME="2025-02-25 12:05:32" # Текущее время в UTC

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

# Функция для создания директорий
create_directories() {
    log "BLUE" "📂 Создание директорий..."

    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
}

# Функция для резервного копирования и восстановления .env файла
backup_restore_env() {
    local action=$1

    case $action in
        "backup")
            log "BLUE" "📑 Создание резервной копии .env файла..."
            if [ -f ".env" ]; then
                cp ".env" "$BACKUP_DIR/.env_$(date +%Y%m%d_%H%M%S)"
                log "GREEN" "✅ Резервная копия .env создана: $BACKUP_DIR/.env_$(date +%Y%m%d_%H%M%S)"
            else
                log "YELLOW" "⚠️ Файл .env не найден, пропуск резервного копирования"
            fi
            ;;
        "restore")
            log "BLUE" "📑 Восстановление .env файла..."
            if [ -f "$BACKUP_DIR/.env_$(date +%Y%m%d_%H%M%S)" ]; then
                cp "$BACKUP_DIR/.env_$(date +%Y%m%d_%H%M%S)" ".env"
                log "GREEN" "✅ .env файл восстановлен из: $BACKUP_DIR/.env_$(date +%Y%m%d_%H%M%S)"
            else
                log "YELLOW" "⚠️ Резервная копия .env не найдена, пропуск восстановления"
            fi
            ;;
    esac
}

# Функция для обновления репозитория
update_repo() {
    log "BLUE" "🔄 Обновление репозитория..."

    # Stash local changes to .env
    if git diff --quiet HEAD -- .env; then
        log "BLUE" "No local changes to .env"
    else
        log "BLUE" "Stashing local changes to .env"
        git stash push -u .env
        STASHED="true"
    fi

    git fetch
    git reset --hard origin/main
    log "GREEN" "✅ Репозиторий обновлен"

     # Restore stashed changes to .env
    if [[ "$STASHED" == "true" ]]; then
        log "BLUE" "Restoring stashed changes to .env"
        git stash pop
    fi
    log "GREEN" "✅ Репозиторий обновлен"
}

# Функция для управления конфигурацией .env
manage_env_file() {
    local env_file=".env"
    local env_example=".env.example"
    local created=false

    log "BLUE" "📝 Управление конфигурацией .env..."

    # Выводим текущую директорию
    log "BLUE" "📍 Текущая директория: $(pwd)"

    # Проверяем существование файлов
    if [ ! -f "$env_file" ]; then
        if [ -f "$env_example" ]; then
            cp "$env_example" "$env_file"
            created=true
            log "GREEN" "✅ Создан новый .env файл из примера"
        else
            log "YELLOW" "⚠️ Файл .env.example не найден, создаем базовый .env"
            cat > "$env_file" << EOL
# Конфигурация бота
BOT_TOKEN=
ADMIN_IDS=
CHANNEL_ID=
BOT_NAME=telegram-publisher-bot # Добавлена переменная BOT_NAME

# Настройки форматирования
DEFAULT_FORMAT=markdown
MAX_FILE_SIZE=20971520

# Ссылки
MAIN_BOT_NAME=Основной бот
MAIN_BOT_LINK=
SUPPORT_BOT_NAME=Техподдержка
SUPPORT_BOT_LINK=
CHANNEL_NAME=Канал проекта
CHANNEL_LINK=

# Тестовый режим
TEST_MODE=false
TEST_CHAT_ID=

# Прокси (если нужен)
HTTPS_PROXY=
EOL
            created=true
            log "YELLOW" "⚠️ Создан базовый .env файл"
        fi
    fi

    # Предлагаем отредактировать файл
    read -r -p "Редактировать .env файл сейчас? [Y/n] " response
    response=${response:-Y}
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        if command -v nano &> /dev/null; then
            nano "$env_file"
        else
            vi "$env_file"
        fi
    else
        log "YELLOW" "⚠️ Файл .env необходимо настроить для работы бота."
        return 1
    fi

    log "GREEN" "✅ Конфигурация .env завершена"
    return 0
}

# Функция для управления контейнером
manage_container() {
    local action=$1
    log "BLUE" "🐳 Управление контейнером..."

    # Проверяем, установлена ли переменная BOT_NAME
    if [ -z "$BOT_NAME" ]; then
        log "RED" "❌ Переменная BOT_NAME не установлена. Установите ее в файле .env"
        return 1
    fi

    # Выводим значение переменной BOT_NAME
    log "BLUE" "🔍 BOT_NAME: $BOT_NAME"

    export DOCKER_UID DOCKER_GID
    export CREATED_BY="$CURRENT_USER"
    export CREATED_AT="$CURRENT_TIME"

    case $action in
        "restart")
            log "BLUE" "🔄 Перезапуск контейнера..."
            docker_compose_cmd -f docker/docker-compose.yml down --remove-orphans || force_remove_container
            docker_compose_cmd -f docker/docker-compose.yml up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка контейнера..."
            docker_compose_cmd -f docker/docker-compose.yml down --remove-orphans || force_remove_container
            ;;
        "start")
            log "BLUE" "▶️ Запуск контейнера..."
            if docker ps -a | grep -q "$BOT_NAME"; then
                force_remove_container
            fi
            docker_compose_cmd -f docker/docker-compose.yml up -d
            ;;
    esac

    if [ "$action" = "start" ] || [ "$action" = "restart" ]; then
        log "BLUE" "⏳ Ожидание запуска бота..."
        sleep 5

        if ! docker ps | grep -q "$BOT_NAME"; then
            log "RED" "❌ Ошибка запуска контейнера"
            docker_compose_cmd -f docker/docker-compose.yml logs
            return 1
        fi

        log "GREEN" "✅ Контейнер запущен"
        docker_compose_cmd -f docker/docker-compose.yml logs --tail=10
    fi
}

# Функция для проверки статуса бота
check_bot_status() {
    log "BLUE" "🔍 Проверка статуса бота..."

    # Проверяем, установлена ли переменная BOT_NAME
    if [ -z "$BOT_NAME" ]; then
        log "RED" "❌ Переменная BOT_NAME не установлена. Установите ее в файле .env"
        return 1
    fi

    # Выводим значение переменной BOT_NAME
    log "BLUE" "🔍 BOT_NAME: $BOT_NAME"

    if docker ps | grep -q "$BOT_NAME"; then
        log "GREEN" "✅ Бот запущен"
        docker_compose_cmd -f docker/docker-compose.yml logs --tail=10
    else
        log "RED" "❌ Бот не запущен"
        docker_compose_cmd -f docker/docker-compose.yml logs --tail=20
    fi
}

# Функция для просмотра логов ошибок
show_error_logs() {
    log "BLUE" "❌ Показать логи ошибок..."
    docker_compose_cmd -f docker/docker-compose.yml logs 2>&1 | grep -i "ERROR"
}

# Функция для очистки старых логов и бэкапов
cleanup_old_files() {
    log "BLUE" "🧹 Очистка старых файлов..."

    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t .env_* 2>/dev/null | tail -n +6 | xargs -r rm
        cd ..
    fi

    find "$LOG_DIR" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

    docker system prune -f --volumes >/dev/null 2>&1 || true

    log "GREEN" "✅ Очистка завершена"
}

# Функция для принудительного удаления контейнера
force_remove_container() {
    log "YELLOW" "⚠️ Принудительное удаление контейнера..."
    docker rm -f "$BOT_NAME" >/dev/null 2>&1 || true
}

# Функция для вывода меню
show_menu() {
    echo "
🤖 Telegram Publisher Bot
========================
1. ⬆️ Обновить из репозитория
2. 📝 Создать или редактировать .env файл
3. 🚀 Собрать и запустить контейнер бота
4. ⏹️ Остановить и удалить контейнер бота
5. 📊 Показать логи (все)
6. ❌ Показать логи ошибок
7. 🔄 Перезапустить бота
8. 🧹 Очистить старые логи и бэкапы
0. 🚪 Выйти
"
}

# Основной цикл
while true; do
    show_menu
    read -r -p "Выберите действие (0-8): " choice

    case "$choice" in
        1)
            update_repo
            ;;
        2)
            manage_env_file
            ;;
        3)
            manage_container "start"
            ;;
        4)
            manage_container "stop"
            ;;
        5)
            check_bot_status
            ;;
        6)
            show_error_logs
            ;;
        7)
            manage_container "restart"
            ;;
        8)
            cleanup_old_files
            ;;
        0)
            log "BLUE" "🚪 Выход..."
            exit 0
            ;;
        *)
            log "RED" "❌ Неверный выбор, попробуйте еще раз"
            ;;
    esac
done