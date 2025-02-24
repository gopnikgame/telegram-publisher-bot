import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """Load environment variables from .env file with detailed logging."""
    env_path = Path('/app/.env')
    if not env_path.exists():
        raise FileNotFoundError(f"File not found: {env_path}")
        
    # Загружаем переменные окружения из файла .env
    load_dotenv(env_path)
    
    # Проверяем загрузку BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        with open(env_path) as f:
            print(f"DEBUG: .env contents: {f.read()}")
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