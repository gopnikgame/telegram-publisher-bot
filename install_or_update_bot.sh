#!/bin/bash

# Включаем строгий режим
set -euo pipefail

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
BACKUP_DIR="./backups"
DOCKER_UID=$(id -u)
DOCKER_GID=$(id -g)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CREATED_BY="gopnikgame"
CREATED_AT="2025-02-24 19:32:08"
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

# Функция для записи системной информации
write_system_info() {
    local info_file="./logs/system_info.log"
    mkdir -p "$(dirname "$info_file")"

    {
        echo "=== System Information ==="
        echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        echo "User: $CREATED_BY"
        echo "Installation Date: $CREATED_AT"
        echo "Docker Version: $(docker --version)"
        # Проверяем наличие docker compose plugin
        if command -v docker &> /dev/null && docker compose version &> /dev/null; then
            echo "Docker Compose Version: $(docker compose version)"
        else
            echo "Docker Compose Version: $(docker-compose --version 2>/dev/null || echo 'Not found')"
        fi
        echo "System: $(uname -a)"
        echo "========================="
    } > "$info_file"
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
    log "BLUE" "🔍 Проверка зависимостей..."

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
    local env_file=".env"
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
            local latest_backup
            latest_backup=$(ls -t "$BACKUP_DIR/.env_"* | head -n1)
            log "YELLOW" "⚠️ Восстановление из последнего бэкапа: $latest_backup"
            cp "$latest_backup" "$env_file"
            log "GREEN" "✅ .env файл восстановлен"
        fi
    fi
}

# Функция для настройки прав доступа
setup_permissions() {
    log "BLUE" "🔧 Настройка прав доступа..."

    # Создаем директории
    mkdir -p "./logs"
    mkdir -p "$BACKUP_DIR"

    # Устанавливаем права
    chmod -R 755 .
    chmod -R 777 "./logs"
    [ -f ".env" ] && chmod 600 ".env"

    # Устанавливаем владельца
    chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" .

    log "GREEN" "✅ Права доступа настроены"
}

# Функция для управления конфигурацией .env
manage_env_file() {
    local env_file=".env"
    local env_example=".env.example"
    local created=false

    log "BLUE" "📝 Управление конфигурацией .env..."

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

    # Проверяем и управляем параметрами
    local missing_params=()
    while IFS= read -r line; do
        if [[ $line =~ ^BOT_TOKEN=$ ]]; then
            missing_params+=("BOT_TOKEN")
        fi
        if [[ $line =~ ^ADMIN_IDS=$ ]]; then
            missing_params+=("ADMIN_IDS")
        fi
        if [[ $line =~ ^CHANNEL_ID=$ ]]; then
            missing_params+=("CHANNEL_ID")
        fi
    done < "$env_file"

    # Обработка отсутствующих параметров
    if [ ${#missing_params[@]} -gt 0 ] || [ "$created" = true ]; then
        log "YELLOW" "⚠️ Необходимо настроить следующие параметры:"
        for param in "${missing_params[@]}"; do
            echo "   • $param"
        done

        read -r -p "Настроить параметры сейчас? [Y/n] " response
        response=${response:-Y}
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            if command -v nano &> /dev/null; then
                nano "$env_file"
            else
                vi "$env_file"
            fi
        else
            log "RED" "❌ Бот не будет работать без настроенных параметров"
            return 1
        fi
    fi

    # Устанавливаем правильные права доступа
    chmod 600 "$env_file"
    chown "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$env_file"

    log "GREEN" "✅ Конфигурация .env завершена"
    return 0
}

# Функция для принудительного удаления контейнера
force_remove_container() {
    local container_name="telegram-publisher-bot"
    log "YELLOW" "🔄 Принудительное удаление контейнера..."

    local container_pid
    container_pid=$(docker inspect --format '{{.State.Pid}}' "$container_name" 2>/dev/null || echo "")

    docker stop "$container_name" &>/dev/null || true
    sleep 2

    if docker ps | grep -q "$container_name"; then
        log "YELLOW" "⚠️ Контейнер все еще работает, применяем SIGKILL..."
        if [ -n "$container_pid" ] && [ "$container_pid" != "0" ]; then
            sudo kill -TERM "$container_pid" &>/dev/null || true
            sleep 2
        fi
        docker kill "$container_name" &>/dev/null || true
    fi

    docker rm -f "$container_name" &>/dev/null || true

    if ! docker ps -a | grep -q "$container_name"; then
        log "GREEN" "✅ Контейнер успешно удален"
    else
        log "RED" "❌ Критическая ошибка: невозможно удалить контейнер"
        return 1
    fi
}

# Функция для вызова docker compose
docker_compose_cmd() {
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        # Используем встроенную команду docker compose
        docker compose "$@"
    else
        # Используем старый docker-compose
        docker-compose "$@"
    fi
}

# Функция для управления контейнером
manage_container() {
    local action=$1
    log "BLUE" "🐳 Управление контейнером..."

    export DOCKER_UID DOCKER_GID
    export CREATED_BY="gopnikgame"
    export CREATED_AT="2025-02-24 19:33:35"

    case $action in
        "restart")
            log "BLUE" "🔄 Перезапуск контейнера..."
            docker_compose_cmd down --remove-orphans || force_remove_container
            docker_compose_cmd up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка контейнера..."
            docker_compose_cmd down --remove-orphans || force_remove_container
            ;;
        "start")
            log "BLUE" "▶️ Запуск контейнера..."
            if docker ps -a | grep -q "telegram-publisher-bot"; then
                force_remove_container
            fi
            docker_compose_cmd up -d
            ;;
    esac

    if [ "$action" = "start" ] || [ "$action" = "restart" ]; then
        log "BLUE" "⏳ Ожидание запуска бота..."
        sleep 5

        if ! docker ps | grep -q "telegram-publisher-bot"; then
            log "RED" "❌ Ошибка запуска контейнера"
            docker_compose_cmd logs
            return 1
        fi

        log "GREEN" "✅ Контейнер запущен"
        docker_compose_cmd logs --tail=10
    fi
}

# Функция для проверки статуса бота
check_bot_status() {
    log "BLUE" "🔍 Проверка статуса бота..."

    if docker ps | grep -q "telegram-publisher-bot"; then
        log "GREEN" "✅ Бот запущен"
        docker_compose_cmd logs --tail=10
    else
        log "RED" "❌ Бот не запущен"
        docker_compose_cmd logs --tail=20
    fi
}

# Функция для очистки старых логов и бэкапов
cleanup_old_files() {
    log "BLUE" "🧹 Очистка старых файлов..."

    if [ -d "$BACKUP_DIR" ]; then
        cd "$BACKUP_DIR"
        ls -t .env_* 2>/dev/null | tail -n +6 | xargs -r rm
        cd ..
    fi

    find "./logs" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

    docker system prune -f --volumes >/dev/null 2>&1 || true

    log "GREEN" "✅ Очистка завершена"
}

# Функция для проверки Docker
check_docker() {
    log "BLUE" "🔍 Проверка Docker..."

    if ! docker info >/dev/null 2>&1; then
        log "YELLOW" "⚠️ Docker демон не запущен"
        if systemctl is-active docker >/dev/null 2>&1; then
            log "BLUE" "🔄 Запуск Docker демона..."
            sudo systemctl start docker
            sleep 3
        else
            log "RED" "❌ Docker ��е установлен или не настроен"
            return 1
        fi
    fi

    if ! docker ps >/dev/null 2>&1; then
        log "YELLOW" "⚠️ Недостаточно прав для работы с Docker"
        if ! groups | grep -q docker; then
            log "BLUE" "🔧 Добавление пользователя в группу docker..."
            sudo usermod -aG docker "${SUDO_USER:-$USER}"
            log "YELLOW" "⚠️ Требуется перезайти в систему"
            return 1
        fi
    fi

    log "GREEN" "✅ Docker настроен корректно"
    return 0
}

# Функция настройки репозитория
setup_repository() {
    log "BLUE" "🔧 Настройка репозитория..."

    if ! command -v git &>/dev/null; then
        log "RED" "❌ Git не установлен"
        return 1
    fi

    if [ -z "$(git config --global user.name)" ]; then
        git config --global user.name "Telegram Publisher Bot"
    fi
    if [ -z "$(git config --global user.email)" ]; then
        git config --global user.email "bot@localhost"
    fi

    if [ ! -f ".gitignore" ]; then
        cat > ".gitignore" << EOL
.env
logs/
backups/
__pycache__/
*.pyc
.DS_Store
EOL
        log "GREEN" "✅ Создан .gitignore файл"
    fi

    log "GREEN" "✅ Репозиторий настроен"
    return 0
}

# Функция для обновления репозитория
update_repo() {
    log "BLUE" "🔄 Обновление репозитория..."

    backup_restore_env "backup"

    if [ -d ".git" ]; then
        git fetch
        git reset --hard origin/main
        log "GREEN" "✅ Репозиторий обновлен"
    else
        git clone "$REPO_URL" .
        log "GREEN" "✅ Репозиторий склонирован"
    fi

    backup_restore_env "restore"
}

# Функция главного меню
main_menu() {
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
                log "BLUE" "🚀 Запуск установки..."
                update_repo
                if ! manage_env_file; then
                    log "RED" "❌ Установка прервана из-за проблем с конфигурацией"
                    continue
                fi
                setup_permissions
                manage_container "start"
                check_bot_status
                ;;
            3)
                log "BLUE" "📜 Показ всех логов (Ctrl+C для выхода):"
                tail -f "./logs/bot.log"
                ;;
            4)
                log "BLUE" "❌ Показ логов ошибок (Ctrl+C для выхода):"
                tail -f "./logs/error.log"
                ;;
            5)
                manage_container "restart"
                check_bot_status
                ;;
            6)
                manage_container "stop"
                log "GREEN" "✅ Бот остановлен!"
                ;;
            7)
                check_bot_status
                ;;
            8)
                update_repo
                setup_permissions
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
}


# Проверяем, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then
    log "RED" "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверяем и устанавливаем зависимости
install_dependencies

# Клонируем репозиторий, если его нет
if [ ! -d "./.git" ]; then
    log "BLUE" "⬇️ Клонирование репозитория..."
    git clone "$REPO_URL" .
else
    log "BLUE" "🔄 Репозиторий уже существует. Обновление..."
    update_repo
fi

# Проверяем наличие необходимых файлов
if [ ! -f "docker-compose.yml" ] && [ ! -f ".env.example" ]; then
    log "RED" "❌ Не найдены необходимые файлы проекта (docker-compose.yml или .env.example)"
    exit 1
fi

# Проверяем Docker
if ! check_docker; then
    log "RED" "❌ Ошибка настройки Docker"
    exit 1
fi

# Настраиваем репозиторий
if ! setup_repository; then
    log "RED" "❌ Ошибка настройки репозитория"
    exit 1
fi

# Записываем системную информацию
write_system_info

# Запускаем главное меню
main_menu
