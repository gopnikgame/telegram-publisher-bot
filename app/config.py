import os
from dotenv import load_dotenv
import re

# Загрузка переменных окружения из .env файла
load_dotenv()

def parse_markdown_link(link_str):
    """Парсит markdown-ссылку и возвращает кортеж (название, URL)."""
    if not link_str:
        return '', ''
    match = re.match(r'\[(.*?)\]\((.*?)\)', link_str)
    if match:
        return match.group(1), match.group(2)
    return '', link_str

class Config:
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # ID администраторов (список)
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
    
    # ID канала для публикации
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    
    # Максимальный размер файла (в байтах)
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 20 * 1024 * 1024))  # 20MB по умолчанию
    
    # Формат сообщений по умолчанию
    DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'plain').lower()
    
    # Прокси
    HTTPS_PROXY = os.getenv('HTTPS_PROXY')
    
    # Ссылки
    MAIN_BOT_NAME, MAIN_BOT_LINK = parse_markdown_link(os.getenv('MAIN_BOT_LINK', ''))
    SUPPORT_BOT_NAME, SUPPORT_BOT_LINK = parse_markdown_link(os.getenv('SUPPORT_BOT_LINK', ''))
    CHANNEL_NAME, CHANNEL_LINK = parse_markdown_link(os.getenv('CHANNEL_LINK', ''))