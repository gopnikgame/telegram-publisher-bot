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

        # Формат сообщений (markdown, html, plain, modern)
        self.DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "modern").lower()
        if self.DEFAULT_FORMAT not in ["markdown", "html", "plain", "modern"]:
            self.DEFAULT_FORMAT = "modern"

        # Настройки прокси
        self.HTTPS_PROXY = os.getenv('HTTPS_PROXY')
        if self.HTTPS_PROXY:
            os.environ['https_proxy'] = self.HTTPS_PROXY

    def create_links(self, format_type=None):
        """Создает строку с гиперссылками в заданном формате."""
        format_type = format_type or self.DEFAULT_FORMAT

        if format_type == "modern":
            return f"\n\n{self.MAIN_BOT_LINK}\n{self.SUPPORT_BOT_LINK}\n{self.CHANNEL_LINK}"
        elif format_type == "html":
            return (
                f"\n\n{self.MAIN_BOT_LINK.replace('[', '<a href=\"').replace(']', '\">').replace(')', '</a>')}\n"
                f"{self.SUPPORT_BOT_LINK.replace('[', '<a href=\"').replace(']', '\">').replace(')', '</a>')}\n"
                f"{self.CHANNEL_LINK.replace('[', '<a href=\"').replace(']', '\">').replace(')', '</a>')}"
            )
        elif format_type == "markdown":
            return f"\n\n{self.MAIN_BOT_LINK}\n{self.SUPPORT_BOT_LINK}\n{self.CHANNEL_LINK}"
        else:  # plain
            return (
                f"\n\n{self.MAIN_BOT_LINK.split('](')[0][1:]}: {self.MAIN_BOT_LINK.split('](')[1][:-1]}\n"
                f"{self.SUPPORT_BOT_LINK.split('](')[0][1:]}: {self.SUPPORT_BOT_LINK.split('](')[1][:-1]}\n"
                f"{self.CHANNEL_LINK.split('](')[0][1:]}: {self.CHANNEL_LINK.split('](')[1][:-1]}"
            )