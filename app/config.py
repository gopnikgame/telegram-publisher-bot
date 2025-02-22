import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not self.BOT_TOKEN:
            raise ValueError("Не установлен BOT_TOKEN")

        self.CHANNEL_ID = os.getenv("CHANNEL_ID")
        if not self.CHANNEL_ID:
            raise ValueError("Не установлен CHANNEL_ID")

        # Ссылки
        self.MAIN_BOT_LINK = os.getenv("MAIN_BOT_LINK")
        self.SUPPORT_BOT_LINK = os.getenv("SUPPORT_BOT_LINK")
        self.CHANNEL_LINK = os.getenv("CHANNEL_LINK")

        # Администраторы
        self.ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
        if not self.ADMIN_IDS:
            raise ValueError("Не установлены ADMIN_IDS")

        # Настройки прокси
        self.HTTPS_PROXY = os.getenv('HTTPS_PROXY')
        if self.HTTPS_PROXY:
            os.environ['https_proxy'] = self.HTTPS_PROXY

    def create_links(self):
        """Создает строку с гиперссылками."""
        return (
            f"\n\n{self.MAIN_BOT_LINK}\n"
            f"{self.SUPPORT_BOT_LINK}\n"
            f"{self.CHANNEL_LINK}"
        )