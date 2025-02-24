import os
from pathlib import Path
from dotenv import load_dotenv

# Явно указываем путь к .env файлу
ENV_PATH = Path('/app/.env')

def load_env():
    """Load environment variables from .env file with detailed logging."""
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"File not found: {ENV_PATH}")
    
    # Загружаем переменные окружения из файла .env с явным указанием пути
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    
    # Проверяем загрузку BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        with open(ENV_PATH) as f:
            content = f.read()
            print(f"DEBUG: Content length: {len(content)}")
            print(f"DEBUG: BOT_TOKEN line: {[line for line in content.splitlines() if 'BOT_TOKEN' in line]}")
        raise ValueError("BOT_TOKEN not found in environment variables")

# Загружаем конфигурацию
load_env()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен в .env файле")
        
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]
    CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
    
    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'markdown')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 20 * 1024 * 1024))  # 20MB by default
    
    MAIN_BOT_NAME = os.getenv('MAIN_BOT_NAME', 'Основной бот')
    MAIN_BOT_LINK = os.getenv('MAIN_BOT_LINK', '')
    SUPPORT_BOT_NAME = os.getenv('SUPPORT_BOT_NAME', 'Техподдержка')
    SUPPORT_BOT_LINK = os.getenv('SUPPORT_BOT_LINK', '')
    CHANNEL_NAME = os.getenv('CHANNEL_NAME', 'Канал проекта')
    CHANNEL_LINK = os.getenv('CHANNEL_LINK', '')
    
    TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
    TEST_CHAT_ID = int(os.getenv('TEST_CHAT_ID', 0))
    
    HTTPS_PROXY = os.getenv('HTTPS_PROXY')

config = Config()