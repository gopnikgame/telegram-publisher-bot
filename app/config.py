import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    MAIN_BOT_LINK = os.getenv('MAIN_BOT_LINK', '')
    SUPPORT_BOT_LINK = os.getenv('SUPPORT_BOT_LINK', '')
    CHANNEL_LINK = os.getenv('CHANNEL_LINK', '')
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'modern')
    HTTPS_PROXY = os.getenv('HTTPS_PROXY')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 20)) * 1024 * 1024  # MB to bytes