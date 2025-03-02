import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    """
    Класс для хранения конфигурационных настроек бота.
    """

    def __init__(self):
        # Основные настройки бота
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not self.BOT_TOKEN:
            logger.error("BOT_TOKEN не установлен в .env файле")
            raise ValueError("BOT_TOKEN не установлен в .env файле")

        self.ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        if not self.ADMIN_IDS:
            logger.error("ADMIN_IDS не установлены в .env файле")
            raise ValueError("ADMIN_IDS не установлены в .env файле")

        self.CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
        if self.CHANNEL_ID == 0 and not os.getenv("TEST_MODE", "false").lower() == "true":
            logger.error("CHANNEL_ID не установлен в .env файле")
            raise ValueError("CHANNEL_ID не установлен в .env файле")

        # Настройки форматирования
        self.DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "markdown")
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB по умолчанию

        # Ссылки для подписи сообщений
        self.MAIN_BOT_NAME = os.getenv("MAIN_BOT_NAME", "Основной бот")
        self.MAIN_BOT_LINK = os.getenv("MAIN_BOT_LINK", "")
        self.SUPPORT_BOT_NAME = os.getenv("SUPPORT_BOT_NAME", "Техподдержка")
        self.SUPPORT_BOT_LINK = os.getenv("SUPPORT_BOT_LINK", "")
        self.CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Канал проекта")
        self.CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")

        # Тестовый режим
        self.TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
        self.TEST_CHAT_ID = int(os.getenv("TEST_CHAT_ID", 0))

        # Прокси (если нужен)
        self.HTTPS_PROXY = os.getenv("HTTPS_PROXY")

        logger.info("Конфигурация успешно загружена")

# Создаем экземпляр конфигурации
config = Config()