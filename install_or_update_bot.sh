#!/bin/bash

set -e

# Конфигурация
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot.git"
TARGET_DIR="/opt/telegram-publisher-bot"
DOCKER_UID=$(id -u)
DOCKER_GID=$(id -g)

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для проверки наличия команды
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ Ошибка: команда $1 не найдена${NC}"
        echo "📦 Установите необходимые зависимости:"
        echo "sudo apt-get update && sudo apt-get install -y $2"
        exit 1
    fi
}

# Функция для установки зависимостей
install_dependencies() {
    echo -e "\n🔍 Проверка зависимостей..."
    
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
        echo -e "${YELLOW}⚠️ Отсутствуют необходимые зависимости${NC}"
        echo "📦 Установка зависимостей..."
        sudo apt-get update
        sudo apt-get install -y "${missing_deps[@]}"
    fi
    
    echo -e "${GREEN}✅ Все зависимости установлены${NC}"
}

# Функция для настройки прав доступа
setup_permissions() {
    local target_dir="$1"
    echo "🔧 Настройка прав доступа..."
    
    # Создаем директории
    mkdir -p "$target_dir/logs"
    
    # Устанавливаем права
    chmod -R 755 "$target_dir"
    chmod -R 777 "$target_dir/logs"
    
    # Устанавливаем владельца
    chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$target_dir"
    
    echo -e "${GREEN}✅ Права доступа настроены${NC}"
}

# Функция для создания/редактирования .env файла
manage_env_file() {
    local env_file="$TARGET_DIR/.env"
    local env_example="$TARGET_DIR/.env.example"
    
    if [ ! -f "$env_file" ]; then
        if [ -f "$env_example" ]; then
            cp "$env_example" "$env_file"
            echo -e "${GREEN}✅ Создан новый .env файл из примера${NC}"
        else
            echo -e "${RED}❌ Файл .env.example не найден${NC}"
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

# Функция для клонирования/обновления репозитория
update_repo() {
    echo "🔄 Обновление репозитория..."
    
    if [ -d "$TARGET_DIR/.git" ]; then
        cd "$TARGET_DIR"
        git fetch
        git reset --hard origin/main
        echo -e "${GREEN}✅ Репозиторий обновлен${NC}"
    else
        git clone "$REPO_URL" "$TARGET_DIR"
        echo -e "${GREEN}✅ Репозиторий склонирован${NC}"
    fi
}

# Функция для сборки и запуска Docker
build_and_run() {
    echo "🏗️ Сборка и запуск контейнеров..."
    
    cd "$TARGET_DIR"
    
    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Файл .env не найден${NC}"
        manage_env_file
    fi
    
    # Останавливаем предыдущие контейнеры
    docker-compose down
    
    # Собираем и запускаем
    docker-compose up --build -d
    
    echo -e "${GREEN}✅ Контейнеры запущены${NC}"
}

# Функция для проверки статуса бота
check_bot_status() {
    echo "🔍 Проверка статуса бота..."
    
    if docker-compose ps | grep -q "telegram-publisher-bot"; then
        echo -e "${GREEN}✅ Бот успешно работает${NC}"
        docker-compose logs --tail=10
    else
        echo -e "${RED}❌ Бот не запущен${NC}"
        echo "Проверьте логи для деталей:"
        docker-compose logs --tail=20
    fi
}

# Основной скрипт
echo -e "${GREEN}🤖 Установка/обновление Telegram Publisher Bot${NC}"

# Проверяем root права
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запустите скрипт с правами root (sudo)${NC}"
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
    echo "6. ⭕ Остановить бота"
    echo "7. 📈 Статус бота"
    echo "8. ⬆️ Обновить из репозитория"
    echo "9. 🚪 Выйти"
    
    read -r -p "Выберите действие (1-9): " choice
    
    case $choice in
        1)
            manage_env_file
            ;;
        2)
            update_repo
            setup_permissions "$TARGET_DIR"
            build_and_run
            check_bot_status
            ;;
        3)
            echo "📜 Показ всех логов (Ctrl+C для выхода):"
            tail -f "$TARGET_DIR/logs/bot.log"
            ;;
        4)
            echo "❌ Показ логов ошибок (Ctrl+C для выхода):"
            tail -f "$TARGET_DIR/logs/error.log"
            ;;
        5)
            echo "🔄 Перезапуск бота..."
            cd "$TARGET_DIR"
            docker-compose restart
            echo -e "${GREEN}✅ Бот перезапущен!${NC}"
            check_bot_status
            ;;
        6)
            echo "⏹️ Остановка бота..."
            cd "$TARGET_DIR"
            docker-compose down
            echo -e "${GREEN}✅ Бот остановлен!${NC}"
            ;;
        7)
            cd "$TARGET_DIR"
            check_bot_status
            ;;
        8)
            update_repo
            setup_permissions "$TARGET_DIR"
            echo -e "${GREEN}✅ Репозиторий обновлен!${NC}"
            read -r -p "Хотите перезапустить бота? [y/N] " response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                cd "$TARGET_DIR"
                docker-compose restart
                check_bot_status
            fi
            ;;
        9)
            echo -e "${GREEN}👋 До свидания!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Неверный выбор. Попробуйте снова.${NC}"
            ;;
    esac
done