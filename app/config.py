import os
from typing import List, Optional

class Config:
    def __init__(self):
        self.BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
        self.ADMIN_IDS: List[str] = os.getenv('ADMIN_IDS', '').split(',')
        self.CHANNEL_ID: str = os.getenv('CHANNEL_ID', '')
        
        # Настройки форматирования
        self.DEFAULT_FORMAT: str = os.getenv('DEFAULT_FORMAT', 'markdown')
        self.MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', '20971520'))  # 20MB по умолчанию
        
        # Ссылки
        self.MAIN_BOT_LINK: Optional[str] = os.getenv('MAIN_BOT_LINK')
        self.MAIN_BOT_NAME: Optional[str] = os.getenv('MAIN_BOT_NAME', 'Основной бот')
        self.SUPPORT_BOT_LINK: Optional[str] = os.getenv('SUPPORT_BOT_LINK')
        self.SUPPORT_BOT_NAME: Optional[str] = os.getenv('SUPPORT_BOT_NAME', 'Техподдержка')
        self.CHANNEL_LINK: Optional[str] = os.getenv('CHANNEL_LINK')
        self.CHANNEL_NAME: Optional[str] = os.getenv('CHANNEL_NAME', 'Канал проекта')
        
        # Тестовый режим
        self._test_mode: bool = os.getenv('TEST_MODE', 'false').lower() == 'true'
        self.TEST_CHAT_ID: Optional[str] = os.getenv('TEST_CHAT_ID')
        
        # Прокси
        self.HTTPS_PROXY: Optional[str] = os.getenv('HTTPS_PROXY')

    @property
    def TEST_MODE(self) -> bool:
        return self._test_mode

    @TEST_MODE.setter
    def TEST_MODE(self, value: bool):
        self._test_mode = value

config = Config()