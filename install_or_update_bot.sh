#!/bin/bash

# Текущая дата и время в UTC для меток
CREATED_AT="2025-02-24 13:35:56"
CREATED_BY="gopnikgame"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функция для логирования
log() {
    local color=$1
    local message=$2
    echo -e "${!color}${message}${NC}"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log "RED" "❌ Docker не установлен"
        return 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        log "RED" "❌ Docker Compose не установлен"
        return 1
    fi
    return 0
}

# Функция для обновления конфигурации
update_config() {
    log "BLUE" "🔧 Настройка конфигурации..."
    
    # Создаем .env если его нет
    if [ ! -f .env ]; then
        cat > .env << EOL
BOT_TOKEN=
ADMIN_IDS=
CHANNEL_ID=
DEFAULT_FORMAT=markdown
MAX_FILE_SIZE=20971520
MAIN_BOT_NAME=Основной бот
MAIN_BOT_LINK=
SUPPORT_BOT_NAME=Техподдержка
SUPPORT_BOT_LINK=
CHANNEL_NAME=Канал проекта
CHANNEL_LINK=
TEST_MODE=false
TEST_CHAT_ID=
HTTPS_PROXY=
EOL
    fi
    
    # Редактируем конфигурацию
    while true; do
        log "BLUE" "📝 Текущие настройки:"
        while IFS='=' read -r key value; do
            if [[ $key == "BOT_TOKEN" ]]; then
                if [ -n "$value" ]; then
                    log "GREEN" "✓ BOT_TOKEN: установлен (длина: ${#value} символов)"
                else
                    log "RED" "✗ BOT_TOKEN: не установлен"
                fi
            else
                log "BLUE" "$key: $value"
            fi
        done < .env
        
        log "YELLOW" "
Выберите действие:
1. Изменить BOT_TOKEN
2. Изменить ADMIN_IDS
3. Изменить CHANNEL_ID
4. Изменить другие настройки
5. Сохранить и выйти"
        
        read -p "Ваш выбор: " choice
        case $choice in
            1)
                read -p "Введите BOT_TOKEN: " token
                sed -i "s/^BOT_TOKEN=.*/BOT_TOKEN=$token/" .env
                ;;
            2)
                read -p "Введите ADMIN_IDS (через запятую): " admins
                sed -i "s/^ADMIN_IDS=.*/ADMIN_IDS=$admins/" .env
                ;;
            3)
                read -p "Введите CHANNEL_ID: " channel
                sed -i "s/^CHANNEL_ID=.*/CHANNEL_ID=$channel/" .env
                ;;
            4)
                ${EDITOR:-nano} .env
                ;;
            5)
                break
                ;;
            *)
                log "RED" "❌ Неверный выбор"
                ;;
        esac
    done
    
    log "BLUE" "✅ Конфигурация .env завершена"
    
    # Устанавливаем права доступа
    log "BLUE" "🔧 Настройка прав доступа..."
    chmod 600 .env
    log "GREEN" "✅ Права доступа настроены"
    
    return 0
}

# Функция для управления контейнером
manage_container() {
    local action=$1
    log "BLUE" "🐳 Управление контейнером..."
    
    case $action in
        "restart")
            log "BLUE" "🔄 Перезапуск контейнера..."
            docker-compose down
            docker-compose up -d
            ;;
        "stop")
            log "BLUE" "⏹️ Остановка контейнера..."
            docker-compose down
            ;;
        "start")
            # Проверка конфигурации
            log "BLUE" "🔍 Проверка конфигурации .env..."
            if [ ! -f .env ]; then
                log "RED" "❌ Файл .env не найден"
                return 1
            fi

            # Выводим текущие настройки
            log "BLUE" "📝 Текущие настройки:"
            while IFS='=' read -r key value; do
                if [[ $key == "BOT_TOKEN" ]]; then
                    if [ -n "$value" ]; then
                        log "GREEN" "✓ BOT_TOKEN: установлен (длина: ${#value} символов)"
                    else
                        log "RED" "✗ BOT_TOKEN: не установлен"
                        return 1
                    fi
                else
                    log "BLUE" "$key: $value"
                fi
            done < .env

            # Проверка монтирования .env
            log "BLUE" "🔍 Проверка монтирования .env..."

            # Запуск контейнера
            log "BLUE" "▶️ Запуск контейнера..."
            if docker ps -a | grep -q "telegram-publisher-bot"; then
                force_remove_container
            fi
            docker-compose up -d
            ;;
    esac
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log "GREEN" "✅ Операция успешно выполнена"
        
        if [ "$action" = "start" ] || [ "$action" = "restart" ]; then
            local max_attempts=6
            local attempt=1
            
            while [ $attempt -le $max_attempts ]; do
                log "BLUE" "🔍 Проверка состояния контейнера (попытка $attempt из $max_attempts)..."
                sleep 5
                
                if ! docker ps | grep -q "telegram-publisher-bot"; then
                    log "RED" "❌ Контейнер не запущен"
                    return 1
                fi
                
                if docker logs telegram-publisher-bot 2>&1 | grep -q "BOT_TOKEN не установлен"; then
                    log "RED" "❌ Контейнер в нерабочем состоянии"
                    docker-compose logs
                    return 1
                fi
                
                if docker logs telegram-publisher-bot 2>&1 | grep -q "Бот успешно запущен"; then
                    log "GREEN" "✅ Контейнер работает корректно"
                    break
                fi
                
                log "YELLOW" "⚠️ Контейнер запускается..."
                attempt=$((attempt + 1))
            done
            
            if [ $attempt -gt $max_attempts ]; then
                log "RED" "❌ Превышено время ожидания запуска"
                docker-compose logs
                return 1
            fi
        fi
    else
        log "RED" "❌ Ошибка при выполнении операции (код: $exit_code)"
        docker-compose logs
        return 1
    fi
    
    return 0
}

# Функция для принудительного удаления контейнера
force_remove_container() {
    log "BLUE" "🔄 Принудительное удаление контейнера..."
    docker rm -f telegram-publisher-bot > /dev/null 2>&1
    log "GREEN" "✅ Контейнер успешно удален"
}

# Основное меню
main_menu() {
    while true; do
        log "BLUE" "
🤖 Telegram Publisher Bot - Управление (Автор: $CREATED_BY, Обновлено: $CREATED_AT)

Выберите действие:
1. Настроить конфигурацию
2. Запустить бота
3. Перезапустить бота
4. Остановить бота
5. Показать логи
6. Обновить бота
7. Выход"
        
        read -p "Ваш выбор: " choice
        case $choice in
            1)
                update_config
                ;;
            2)
                manage_container "start"
                ;;
            3)
                manage_container "restart"
                ;;
            4)
                manage_container "stop"
                ;;
            5)
                docker-compose logs --tail=100 -f
                ;;
            6)
                log "BLUE" "🔄 Обновление бота..."
                git pull
                docker-compose build --no-cache
                manage_container "restart"
                ;;
            7)
                log "GREEN" "👋 До свидания!"
                exit 0
                ;;
            *)
                log "RED" "❌ Неверный выбор"
                ;;
        esac
    done
}

# Проверяем наличие Docker
if ! check_docker; then
    exit 1
fi

# Запускаем основное меню
main_menu