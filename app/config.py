from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging
import os
import re
from typing import List, Optional, Tuple

load_dotenv()
logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Ошибка валидации конфигурации"""
    pass

def parse_markdown_link(link_str: Optional[str]) -> Tuple[str, str]:
    """Парсит markdown-ссылку и возвращает кортеж (название, URL)."""
    if not link_str:
        return '', ''
    match = re.match(r'\[(.*?)\]\((.*?)\)', link_str)
    if match:
        return match.group(1), match.group(2)
    return '', link_str

def validate_telegram_id(id_str: str) -> bool:
    """Проверяет корректность Telegram ID."""
    return bool(re.match(r'^-?\d+$', id_str.strip()))

def get_admin_ids() -> List[str]:
    """Получает список ID администраторов из переменной окружения."""
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    return [aid.strip() for aid in admin_ids if aid.strip()]

@dataclass
class Config:
    """Конфигурация бота с валидацией и значениями по умолчанию"""
    
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv('BOT_TOKEN', ''))
    ADMIN_IDS: List[str] = field(default_factory=get_admin_ids)
    CHANNEL_ID: str = field(default_factory=lambda: os.getenv('CHANNEL_ID', ''))
    MAX_FILE_SIZE: int = field(
        default_factory=lambda: int(os.getenv('MAX_FILE_SIZE', '20971520'))
    )
    DEFAULT_FORMAT: str = field(
        default_factory=lambda: os.getenv('DEFAULT_FORMAT', 'markdown').lower()
    )
    HTTPS_PROXY: Optional[str] = field(
        default_factory=lambda: os.getenv('HTTPS_PROXY')
    )
    TEST_MODE: bool = field(
        default_factory=lambda: os.getenv('TEST_MODE', 'false').lower() == 'true'
    )
    TEST_CHAT_ID: str = field(
        default_factory=lambda: os.getenv('TEST_CHAT_ID', '')
    )
    
    MAIN_BOT_NAME: str = field(default='')
    MAIN_BOT_LINK: str = field(default='')
    SUPPORT_BOT_NAME: str = field(default='')
    SUPPORT_BOT_LINK: str = field(default='')
    CHANNEL_NAME: str = field(default='')
    CHANNEL_LINK: str = field(default='')
    
    def __post_init__(self):
        """Валидация после инициализации."""
        self.MAIN_BOT_NAME, self.MAIN_BOT_LINK = parse_markdown_link(
            os.getenv('MAIN_BOT_LINK')
        )
        self.SUPPORT_BOT_NAME, self.SUPPORT_BOT_LINK = parse_markdown_link(
            os.getenv('SUPPORT_BOT_LINK')
        )
        self.CHANNEL_NAME, self.CHANNEL_LINK = parse_markdown_link(
            os.getenv('CHANNEL_LINK')
        )
        
        if not self.BOT_TOKEN:
            raise ConfigValidationError("BOT_TOKEN не установлен")
        
        if not self.ADMIN_IDS:
            raise ConfigValidationError("ADMIN_IDS не установлен")
            
        for admin_id in self.ADMIN_IDS:
            if not validate_telegram_id(admin_id):
                raise ConfigValidationError(f"Некорректный ADMIN_ID: {admin_id}")
        
        if not self.CHANNEL_ID:
            raise ConfigValidationError("CHANNEL_ID не установлен")
        elif not validate_telegram_id(self.CHANNEL_ID):
            raise ConfigValidationError("Некорректный CHANNEL_ID")
        
        if self.TEST_CHAT_ID and not validate_telegram_id(self.TEST_CHAT_ID):
            raise ConfigValidationError("Некорректный TEST_CHAT_ID")
        
        if self.DEFAULT_FORMAT not in ['markdown', 'html', 'plain', 'modern']:
            logger.warning(
                f"Неизвестный формат сообщений: {self.DEFAULT_FORMAT}, "
                "используется markdown"
            )
            self.DEFAULT_FORMAT = 'markdown'

# Создание экземпляра конфигурации
try:
    config = Config()
except ConfigValidationError as e:
    logger.critical(f"Ошибка загрузки конфигурации: {e}")
    raise