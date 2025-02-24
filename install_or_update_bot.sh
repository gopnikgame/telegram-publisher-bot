#!/bin/bash

set -e  # Останавливаем скрипт при любой ошибке

# Получаем текущего пользователя и его группу
DOCKER_UID=$(id -u)
DOCKER_GID=$(id -g)

# Функция для проверки наличия команды в системе
function check_command() {
    command -v "$1" >/dev/null 2>&1 || { echo >&2 "$1 не установлен. Устанавливаю..."; install_command "$1"; }
}

# Функция для установки команды в системе
function install_command() {
    case "$1" in
        docker)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            rm get-docker.sh
            # Добавляем текущего пользователя в группу docker
            usermod -aG docker "${SUDO_USER:-$USER}"
            ;;
        docker-compose)
            curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
            ;;
        git)
            apt-get update
            apt-get install -y git
            ;;
        *)
            echo "Неизвестная команда для установки: $1"
            exit 1
            ;;
    esac
}

# Функция настройки прав доступа
function setup_permissions() {
    local target_dir="$1"
    echo "🔧 Настройка прав доступа..."
    
    # Создаем директорию для логов, если её нет
    mkdir -p "$target_dir/logs"
    
    # Устанавливаем базовые права на директории и файлы
    chmod -R 755 "$target_dir"
    chmod -R 777 "$target_dir/logs"
    
    # Устанавливаем владельца
    chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$target_dir"
    
    echo "✅ Права доступа настроены"
}

# Проверка root прав
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверка и установка зависимостей
check_command "docker"
check_command "docker-compose"
check_command "git"

# Установка домашней директории текущего пользователя
HOME_DIR=$(eval echo ~${SUDO_USER})
TARGET_DIR="$HOME_DIR/telegram-publisher-bot"

# Сохранение .env файла, если он существует
if [ -f "$TARGET_DIR/.env" ]; then
    echo "💾 Сохранение .env файла..."
    cp "$TARGET_DIR/.env" /tmp/.env.backup
    chown "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" /tmp/.env.backup
fi

# Клонирование или обновление репозитория
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot"

if [ -d "$TARGET_DIR" ]; then
    echo "📂 Папка уже существует. Удаление текущей папки и клонирование заново..."
    rm -rf "$TARGET_DIR"
fi

echo "📥 Клонирование репозитория..."
git clone "$REPO_URL" "$TARGET_DIR"

# Настройка прав доступа для всей директории
setup_permissions "$TARGET_DIR"

# Восстановление .env файла, если он был сохранен
if [ -f "/tmp/.env.backup" ]; then
    echo "💾 Восстановление .env файла..."
    mv /tmp/.env.backup "$TARGET_DIR/.env"
fi

cd "$TARGET_DIR" || exit

# Экспорт переменных окружения для docker-compose с новыми именами
export DOCKER_UID
export DOCKER_GID

# Функция для создания или редактирования .env файла
function manage_env_file() {
    if [ ! -f .env ]; then
        echo ".env файл не найден. Создание нового..."
        cat > .env << EOF
# Конфигурация бота
BOT_TOKEN=
ADMIN_IDS=
CHANNEL_ID=

# Настройки форматирования
DEFAULT_FORMAT=markdown
MAX_FILE_SIZE=20971520

# Ссылки (в формате [название](ссылка))
MAIN_BOT_LINK=
SUPPORT_BOT_LINK=
CHANNEL_LINK=

# Тестовый режим
TEST_MODE=false
TEST_CHAT_ID=

# Прокси (если нужен)
HTTPS_PROXY=
EOF
        chown "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" .env
    fi

    echo "📝 Редактирование .env файла..."
    sudo -u "${SUDO_USER:-$USER}" nano .env
}

# Функция для проверки конфигурации
function check_config() {
    if [ ! -f .env ]; then
        echo "❌ Файл .env не найден!"
        return 1
    fi

    local required_vars=("BOT_TOKEN" "ADMIN_IDS" "CHANNEL_ID")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=." .env; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Отсутствуют обязательные переменные в .env:"
        printf '%s\n' "${missing_vars[@]}"
        return 1
    fi

    return 0
}

# Меню для пользователя
while true; do
    echo -e "\n📱 Telegram Publisher Bot - Меню установки\n"
    echo "1. 📝 Создать или редактировать .env файл"
    echo "2. 🚀 Собрать и запустить бота"
    echo "3. 📊 Показать логи"
    echo "4. 🔄 Перезапустить бота"
    echo "5. ⭕ Остановить бота"
    echo "6. ❌ Выйти"
    read -r -p "Выберите действие (1-6): " choice

    case $choice in
        1)
            manage_env_file
            ;;
        2)
            if ! check_config; then
                echo -e "\n⚠️ Пожалуйста, сначала настройте .env файл (опция 1)"
                continue
            fi

            echo "🔄 Остановка и удаление существующих контейнеров..."
            docker-compose down --remove-orphans

            # Повторная проверка прав доступа перед запуском
            setup_permissions "$TARGET_DIR"

            echo "🔨 Сборка образа..."
            docker-compose build --no-cache

            echo "▶️ Запуск бота..."
            docker-compose up -d

            echo -e "\n✅ Бот успешно запущен!"
            ;;
        3)
            docker-compose logs -f
            ;;
        4)
            echo "🔄 Перезапуск бота..."
            docker-compose restart
            echo "✅ Бот перезапущен!"
            ;;
        5)
            echo "⏹️ Остановка бота..."
            docker-compose down
            echo "✅ Бот остановлен!"
            ;;
        6)
            echo "👋 До свидания!"
            exit 0
            ;;
        *)
            echo "❌ Неверный выбор. Попробуйте снова."
            ;;
    esac
done