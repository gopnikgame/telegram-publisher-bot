import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()


class Config:
    # Основные настройки бота
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен в .env файле")

    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    if not ADMIN_IDS:
        raise ValueError("ADMIN_IDS не установлены в .env файле")

    CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
    if CHANNEL_ID == 0 and not os.getenv("TEST_MODE", "false").lower() == "true":
        raise ValueError("CHANNEL_ID не установлен в .env файле")

    # Настройки форматирования
    DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "markdown")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB по умолчанию

    # Ссылки для подписи сообщений
    MAIN_BOT_NAME = os.getenv("MAIN_BOT_NAME", "Основной бот")
    MAIN_BOT_LINK = os.getenv("MAIN_BOT_LINK", "")
    SUPPORT_BOT_NAME = os.getenv("SUPPORT_BOT_NAME", "Техподдержка")
    SUPPORT_BOT_LINK = os.getenv("SUPPORT_BOT_LINK", "")
    CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Канал проекта")
    CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")

    # Тестовый режим
    TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
    TEST_CHAT_ID = int(os.getenv("TEST_CHAT_ID", 0))

    # Прокси (если нужен)
    HTTPS_PROXY = os.getenv("HTTPS_PROXY")


# Создаем экземпляр конфигурации
config = Config()