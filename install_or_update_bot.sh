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
CREATED_BY="gopnikgame"
CREATED_AT="2025-02-24 11:47:18"

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
    local info_file="$TARGET_DIR/logs/system_info.log"
    mkdir -p "$(dirname "$info_file")"
    
    {
        echo "=== System Information ==="
        echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        echo "User: $CREATED_BY"
        echo "Installation Date: $CREATED_AT"
        echo "Docker Version: $(docker --version)"
        echo "Docker Compose Version: $(docker-compose --version)"
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
    [ -f "$target_dir/.env" ] && chmod 600 "$target_dir/.env"
    
    # Устанавливаем владельца
    chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$target_dir"
    
    log "GREEN" "✅ Права доступа настроены"
}

# Функция для создания/редактирования .env файла
manage_env_file() {
    local env_file="$TARGET_DIR/.env"
    local env_example="$TARGET_DIR/.env.example"
    local created=false
    
    log "BLUE" "📝 Управление конфигурацией .env..."
    
    # Проверяем существование файлов
    if [ ! -f "$env_file" ]; then
        if [ -f "$env_example" ]; then
            cp "$env_example" "$env_file"
            created=true
            log "GREEN" "✅ Создан новый .env файл из примера"
        else
            log "RED" "❌ Файл .env.example не найден"
            # Создаем базовый .env файл
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

    # Проверяем обязательные параметры
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

    # Если есть отсутствующие параметры или файл только что создан
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
            
            # Проверяем, заполнены ли обязательные параметры
            local still_missing=false
            while IFS= read -r line; do
                if [[ $line =~ ^(BOT_TOKEN|ADMIN_IDS|CHANNEL_ID)=$ ]]; then
                    still_missing=true
                    break
                fi
            done < "$env_file"
            
            if [ "$still_missing" = true ]; then
                log "RED" "❌ Обязательные параметры все еще не настроены"
                log "YELLOW" "⚠️ Бот не будет работать без настроенных параметров"
                return 1
            fi
        else
            log "RED" "❌ Бот не будет работать без настроенных параметров"
            return 1
        fi
    else
        # Если все параметры заполнены, спрашиваем о редактировании
        read -r -p "Хотите отредактировать существующие настройки? [y/N] " response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            if command -v nano &> /dev/null; then
                nano "$env_file"
            else
                vi "$env_file"
            fi
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
    
    # Получаем PID процесса внутри контейнера
    local container_pid=$(docker inspect --format '{{.State.Pid}}' "$container_name" 2>/dev/null || echo "")
    
    # Пробуем остановить мягко
    docker stop "$container_name" &>/dev/null || true
    sleep 2
    
    # Проверяем, остановился ли контейнер
    if docker ps | grep -q "$container_name"; then
        log "YELLOW" "⚠️ Контейнер все еще работает, применяем SIGKILL..."
        # Сначала пробуем отправить SIGTERM напрямую процессу
        if [ -n "$container_pid" ] && [ "$container_pid" != "0" ]; then
            sudo kill -TERM "$container_pid" &>/dev/null || true
            sleep 2
        fi
        docker kill "$container_name" &>/dev/null || true
        sleep 2
    fi
    
    # Принудительное удаление
    docker rm -f "$container_name" &>/dev/null || true
    
    # Проверяем, существует ли еще контейнер
    if docker ps -a | grep -q "$container_name"; then
        log "RED" "❌ Не удалось удалить контейнер"
        log "YELLOW" "⚠️ Попытка очистки Docker..."
        
        # Очистка Docker системы
        docker system prune -f &>/dev/null || true
        
        # Последняя попытка удаления
        if docker rm -f "$container_name" &>/dev/null; then
            log "GREEN" "✅ Контейнер успешно удален"
        else
            log "RED" "❌ Критическая ошибка: невозможно удалить контейнер"
            log "YELLOW" "⚠️ Рекомендуется перезагрузить систему"
            return 1
        fi
    else
        log "GREEN" "✅ Контейнер успешно удален"
    fi
}

# Функция для управления контейнером
manage_container() {
    local action=$1
    log "BLUE" "🐳 Управление контейнером..."
    
    cd "$TARGET_DIR"
    
    # Экспортируем переменные окружения
    export DOCKER_UID DOCKER_GID
    export CREATED_BY="gopnikgame"
    export CREATED_AT="2025-02-24 12:16:29"
    
    # Проверка конфигурации перед запуском/перезапуском
    if [ "$action" = "start" ] || [ "$action" = "restart" ]; then
        if [ ! -f "$TARGET_DIR/.env" ]; then
            log "RED" "❌ Файл .env не найден"
            log "YELLOW" "⚠️ Сначала настройте конфигурацию (пункт 1 в меню)"
            return 1
        fi

        # Детальная проверка .env файла
        log "BLUE" "🔍 Проверка конфигурации .env..."
        
        # Проверяем формат файла и конвертируем при необходимости
        if file "$TARGET_DIR/.env" | grep -q "CRLF"; then
            log "YELLOW" "⚠️ Обнаружен CRLF формат, конвертируем в Unix формат..."
            tr -d '\r' < "$TARGET_DIR/.env" > "$TARGET_DIR/.env.tmp" && mv "$TARGET_DIR/.env.tmp" "$TARGET_DIR/.env"
        fi

        # Проверяем кодировку
        if file -i "$TARGET_DIR/.env" | grep -qv "charset=utf-8"; then
            log "YELLOW" "⚠️ Конвертируем файл в UTF-8..."
            iconv -f $(file -i "$TARGET_DIR/.env" | grep -o "charset=.*" | cut -d= -f2) -t UTF-8 "$TARGET_DIR/.env" > "$TARGET_DIR/.env.tmp" && mv "$TARGET_DIR/.env.tmp" "$TARGET_DIR/.env"
        fi

        # Создаем резервную копию .env для сравнения после монтирования
        cp "$TARGET_DIR/.env" "$TARGET_DIR/.env.check"

        # Проверяем содержимое .env
        local bot_token=""
        local has_errors=false
        
        log "BLUE" "📝 Текущие настройки:"
        while IFS='=' read -r key value; do
            if [[ $key == \#* ]] || [[ -z $key ]]; then
                continue
            fi
            if [[ $key == "BOT_TOKEN" ]]; then
                if [[ -n $value ]]; then
                    bot_token=$value
                    log "GREEN" "✓ BOT_TOKEN: установлен (длина: ${#value} символов)"
                    # Проверяем формат токена
                    if ! [[ $value =~ ^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$ ]]; then
                        log "RED" "❌ Внимание: формат BOT_TOKEN может быть некорректным"
                        has_errors=true
                    fi
                else
                    log "RED" "✗ BOT_TOKEN: не установлен"
                    has_errors=true
                fi
            else
                log "BLUE" "$key: $value"
            fi
        done < "$TARGET_DIR/.env"

        if [ "$has_errors" = true ]; then
            log "RED" "❌ Обнаружены ошибки в конфигурации"
            return 1
        fi

        # Проверяем права доступа и владельца
        local env_perms=$(stat -c %a "$TARGET_DIR/.env")
        local env_owner=$(stat -c %U:%G "$TARGET_DIR/.env")
        if [ "$env_perms" != "600" ]; then
            log "YELLOW" "⚠️ Исправление прав доступа для .env ($env_perms -> 600)..."
            chmod 600 "$TARGET_DIR/.env"
        fi
        if [ "$env_owner" != "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" ]; then
            log "YELLOW" "⚠️ Исправление владельца для .env..."
            chown "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$TARGET_DIR/.env"
        fi

        # Проверяем монтирование с помощью временного контейнера
        log "BLUE" "🔍 Проверка монтирования .env..."
        if ! docker run --rm -v "$TARGET_DIR/.env:/app/.env:ro" alpine sh -c 'cat /app/.env | grep "BOT_TOKEN" > /dev/null'; then
            log "RED" "❌ Ошибка при проверке монтирования .env"
            rm -f "$TARGET_DIR/.env.check"
            return 1
        fi
    fi
    
    case $action in
        "restart")
            log "BLUE" "🔄 Перезапуск контейнера..."
            docker-compose down --remove-orphans --timeout 30 || force_remove_container
            sleep 2
            docker-compose up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка контейнера..."
            docker-compose down --remove-orphans --timeout 30 || force_remove_container
            ;;
        "start")
            log "BLUE" "▶️ Запуск контейнера..."
            if docker ps -a | grep -q "telegram-publisher-bot"; then
                force_remove_container
            fi
            
            # Проверяем конфигурацию Docker
            if ! docker-compose config --quiet; then
                log "RED" "❌ Ошибка в конфигурации docker-compose"
                rm -f "$TARGET_DIR/.env.check"
                return 1
            fi

            # Запускаем контейнер
            docker-compose up -d
            
            # Ждем запуска и проверяем монтирование
            sleep 2
            if docker exec telegram-publisher-bot sh -c 'test -f /app/.env && cat /app/.env | grep "BOT_TOKEN" > /dev/null'; then
                log "GREEN" "✅ .env файл успешно смонтирован"
                
                # Сравниваем содержимое файла в контейнере с оригиналом
                local container_env=$(docker exec telegram-publisher-bot cat /app/.env)
                local original_env=$(cat "$TARGET_DIR/.env.check")
                
                if [ "$container_env" != "$original_env" ]; then
                    log "RED" "❌ Содержимое .env в контейнере отличается от оригинала"
                    docker-compose down
                    rm -f "$TARGET_DIR/.env.check"
                    return 1
                fi
                
                log "GREEN" "✅ Проверка содержимого .env успешна"
            else
                log "RED" "❌ .env файл не смонтирован или недоступен в контейнере"
                docker-compose down
                rm -f "$TARGET_DIR/.env.check"
                return 1
            fi
            ;;
    esac
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log "GREEN" "✅ Операция успешно выполнена"
        
        if [ "$action" = "start" ] || [ "$action" = "restart" ]; then
            local max_attempts=6
            local attempt=1
            local container_healthy=false
            
            while [ $attempt -le $max_attempts ]; do
                log "BLUE" "🔍 Проверка состояния контейнера (попытка $attempt из $max_attempts)..."
                sleep 5
                
                if ! docker ps | grep -q "telegram-publisher-bot"; then
                    log "RED" "❌ Контейнер не запущен"
                    rm -f "$TARGET_DIR/.env.check"
                    return 1
                fi
                
                local health_status=$(docker inspect --format='{{.State.Health.Status}}' telegram-publisher-bot 2>/dev/null || echo "unknown")
                
                case $health_status in
                    "healthy")
                        log "GREEN" "✅ Контейнер работает корректно"
                        container_healthy=true
                        break
                        ;;
                    "starting")
                        log "YELLOW" "⚠️ Контейнер запускается..."
                        # Проверяем логи на наличие ошибок
                        if docker-compose logs --tail=5 | grep -q "BOT_TOKEN не установлен"; then
                            log "RED" "❌ Ошибка: BOT_TOKEN не читается контейнером"
                            docker exec telegram-publisher-bot sh -c 'cat /app/.env | grep "BOT_TOKEN"' || log "RED" "❌ Невозможно прочитать BOT_TOKEN в контейнере"
                            docker-compose down
                            rm -f "$TARGET_DIR/.env.check"
                            return 1
                        fi
                        ;;
                    "unhealthy")
                        log "RED" "❌ Контейнер в нерабочем состоянии"
                        docker-compose logs --tail=20
                        rm -f "$TARGET_DIR/.env.check"
                        return 1
                        ;;
                    *)
                        log "YELLOW" "⚠️ Статус проверки: $health_status"
                        ;;
                esac
                
                attempt=$((attempt + 1))
            done
            
            if [ "$container_healthy" = false ]; then
                log "YELLOW" "⚠️ Контейнер запущен, но healthcheck не пройден"
                log "YELLOW" "⚠️ Проверьте логи для деталей:"
                docker-compose logs --tail=20
            fi
        fi
    else
        log "RED" "❌ Ошибка при выполнении операции (код: $exit_code)"
        docker-compose logs --tail=20
        rm -f "$TARGET_DIR/.env.check"
        return 1
    fi
    
    # Очистка временных файлов
    rm -f "$TARGET_DIR/.env.check"
}

# Функция для проверки статуса бота
check_bot_status() {
    log "BLUE" "🔍 Проверка статуса бота..."
    
    cd "$TARGET_DIR"
    
    if docker ps | grep -q "telegram-publisher-bot"; then
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' telegram-publisher-bot 2>/dev/null || echo "unknown")
        log "GREEN" "✅ Бот запущен (статус: $health_status)"
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
        ls -t .env_* 2>/dev/null | tail -n +6 | xargs -r rm
    fi
    
    # Очищаем старые логи
    find "$TARGET_DIR/logs" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
    
    # Очищаем старые Docker логи
    docker system prune -f --volumes >/dev/null 2>&1 || true
    
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

# Записываем системную информацию
write_system_info

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
            log "BLUE" "🚀 Запуск установки..."
            update_repo
            if ! manage_env_file; then
                log "RED" "❌ Установка прервана из-за проблем с конфигурацией"
                continue
            fi
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