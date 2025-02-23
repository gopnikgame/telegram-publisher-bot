#!/bin/bash

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
            ;;
        git)
            apt-get update
            apt-get install -y git
            ;;
        *)
            echo "Неизвестная команда для установки: $1"
            ;;
    esac
}

# Проверка и установка зависимостей
check_command "docker"
check_command "git"

# Клонирование или обновление репозитория
REPO_URL="https://github.com/gopnikgame/telegram-publisher-bot"
TARGET_DIR="/root/telegram-publisher-bot"

if [ -d "$TARGET_DIR" ]; then
    echo "Обновление существующего репозитория..."
    cd "$TARGET_DIR" || exit
    git pull
else
    echo "Клонирование репозитория..."
    git clone "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR" || exit

# Функция для создания или редактирования .env файла
function manage_env_file() {
    if [ ! -f .env ]; then
        echo ".env файл не найден. Создание нового..."
        touch .env
    fi

    echo "Редактирование .env файла..."
    nano .env
}

# Меню для пользователя
while true; do
    echo "Выберите действие:"
    echo "1. Создать или редактировать .env файл"
    echo "2. Компилировать и запустить бота"
    echo "3. Выйти"
    read -r choice
    case $choice in
        1)
            manage_env_file
            ;;
        2)
            echo "Остановка и удаление существующих контейнеров..."
            docker-compose down

            echo "Компиляция и запуск контейнеров..."
            docker-compose build
            docker-compose up -d
            ;;
        3)
            exit 0
            ;;
        *)
            echo "Неверный выбор. Попробуйте снова."
            ;;
    esac
done