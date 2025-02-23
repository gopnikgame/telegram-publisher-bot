import os
from dotenv import load_dotenv
import re
from typing import Tuple, List, Optional
from dataclasses import dataclass
import logging

# Загрузка переменных окружения из .env файла
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Ошибка валидации конфигурации"""
    pass

def parse_markdown_link(link_str: Optional[str]) -> Tuple[str, str]:
    """
    Парсит markdown-ссылку и возвращает кортеж (название, URL).
    
    Args:
        link_str (Optional[str]): Строка с markdown-ссылкой
        
    Returns:
        Tuple[str, str]: (название, URL)
    """
    if not link_str:
        return '', ''
    match = re.match(r'\[(.*?)\]\((.*?)\)', link_str)
    if match:
        return match.group(1), match.group(2)
    return '', link_str

def validate_telegram_id(id_str: str) -> bool:
    """
    Проверяет корректность Telegram ID.
    
    Args:
        id_str (str): ID для проверки
        
    Returns:
        bool: True если ID корректный
    """
    return bool(re.match(r'^-?\d+$', id_str.strip()))

def validate_config() -> List[str]:
    """
    Проверяет корректность конфигурации.
    
    Returns:
        List[str]: Список найденных проблем
    """
    problems = []
    
    if not Config.BOT_TOKEN:
        problems.append("BOT_TOKEN не установлен")
    elif not re.match(r'^\d+:[A-Za-z0-9_-]+$', Config.BOT_TOKEN):
        problems.append("Некорректный формат BOT_TOKEN")
    
    if not Config.ADMIN_IDS:
        problems.append("ADMIN_IDS не установлен")
    else:
        for admin_id in Config.ADMIN_IDS:
            if not validate_telegram_id(admin_id):
                problems.append(f"Некорректный ADMIN_ID: {admin_id}")
    
    if not Config.CHANNEL_ID:
        problems.append("CHANNEL_ID не установлен")
    elif not validate_telegram_id(Config.CHANNEL_ID):
        problems.append("Некорректный CHANNEL_ID")
    
    if Config.TEST_CHAT_ID and not validate_telegram_id(Config.TEST_CHAT_ID):
        problems.append("Некорректный TEST_CHAT_ID")
    
    return problems

@dataclass
class Config:
    """Конфигурация бота с валидацией и значениями по умолчанию"""
    
    # Токен бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # ID администраторов (список)
    ADMIN_IDS: List[str] = os.getenv('ADMIN_IDS', '').split(',')
    
    # ID канала для публикации
    CHANNEL_ID: str = os.getenv('CHANNEL_ID', '')
    
    # Максимальный размер файла (в байтах)
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', 20 * 1024 * 1024))  # 20MB по умолчанию
    
    # Формат сообщений по умолчанию
    DEFAULT_FORMAT: str = os.getenv('DEFAULT_FORMAT', 'markdown').lower()
    
    # Прокси
    HTTPS_PROXY: Optional[str] = os.getenv('HTTPS_PROXY')
    
    # Тестовый режим
    TEST_MODE: bool = os.getenv('TEST_MODE', 'false').lower() == 'true'
    TEST_CHAT_ID: str = os.getenv('TEST_CHAT_ID', '')
    
    # Ссылки
    MAIN_BOT_NAME: str
    MAIN_BOT_LINK: str
    SUPPORT_BOT_NAME: str
    SUPPORT_BOT_LINK: str
    CHANNEL_NAME: str
    CHANNEL_LINK: str
    
    @classmethod
    def load(cls):
        """
        Загружает и валидирует конфигурацию.
        
        Raises:
            ConfigValidationError: Если найдены проблемы в конфигурации
        """
        # Парсинг ссылок
        cls.MAIN_BOT_NAME, cls.MAIN_BOT_LINK = parse_markdown_link(os.getenv('MAIN_BOT_LINK', ''))
        cls.SUPPORT_BOT_NAME, cls.SUPPORT_BOT_LINK = parse_markdown_link(os.getenv('SUPPORT_BOT_LINK', ''))
        cls.CHANNEL_NAME, cls.CHANNEL_LINK = parse_markdown_link(os.getenv('CHANNEL_LINK', ''))
        
        # Валидация конфигурации
        problems = validate_config()
        if problems:
            error_msg = "Найдены проблемы в конфигурации:\n" + "\n".join(f"- {p}" for p in problems)
            logger.error(error_msg)
            raise ConfigValidationError(error_msg)
        
        # Очистка списка админов от пустых значений
        cls.ADMIN_IDS = [aid.strip() for aid in cls.ADMIN_IDS if aid.strip()]
        
        # Проверка формата сообщений
        if cls.DEFAULT_FORMAT not in ['markdown', 'html', 'plain', 'modern']:
            logger.warning(f"Неизвестный формат сообщений: {cls.DEFAULT_FORMAT}, используется markdown")
            cls.DEFAULT_FORMAT = 'markdown'
        
        logger.info("Конфигурация загружена успешно")

# Загрузка конфигурации при импорте модуля
try:
    Config.load()
except ConfigValidationError as e:
    logger.critical(f"Ошибка загрузки конфигурации: {e}")
    raise