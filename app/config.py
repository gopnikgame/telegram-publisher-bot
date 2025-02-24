import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    # Основные настройки бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
    
    # Настройки форматирования
    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'markdown')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 20 * 1024 * 1024))  # 20MB by default
    
    # Ссылки для подписи сообщений
    MAIN_BOT_NAME = os.getenv('MAIN_BOT_NAME', 'Основной бот')
    MAIN_BOT_LINK = os.getenv('MAIN_BOT_LINK', '')
    SUPPORT_BOT_NAME = os.getenv('SUPPORT_BOT_NAME', 'Техподдержка')
    SUPPORT_BOT_LINK = os.getenv('SUPPORT_BOT_LINK', '')
    CHANNEL_NAME = os.getenv('CHANNEL_NAME', 'Канал проекта')
    CHANNEL_LINK = os.getenv('CHANNEL_LINK', '')
    
    # Тестовый режим
    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
    TEST_CHAT_ID = int(os.getenv('TEST_CHAT_ID', 0))
    
    # Прокси (если нужен)
    HTTPS_PROXY = os.getenv('HTTPS_PROXY')

config = Config()