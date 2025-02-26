import logging
import os
from telegram.ext import Application
from app.bot import setup_handlers  # Функция для добавления обработчиков
from app.config import config
from app.utils import setup_logging

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

async def main() -> None:
    """Start the bot."""
    logger.info("Инициализация бота...")
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле")
        return

    try:
        # Создаем экземпляр Application
        application = (
            Application.builder()
            .token(config.BOT_TOKEN)
            .connect_timeout(30)  # Таймаут соединения
            .read_timeout(30)     # Таймаут чтения
            .get_updates_connect_timeout(30)  # Таймаут соединения для обновлений
            .get_updates_read_timeout(30)     # Таймаут чтения для обновлений
            .proxy_url(config.HTTPS_PROXY if config.HTTPS_PROXY else None)  # Прокси, если используется
            .build()
        )

        # Настройка обработчиков
        setup_handlers(application)

        # Запуск бота
        logger.info("Бот запускается...")
        await application.run_polling(
            allowed_updates=Application.ALL_UPDATE_TYPES  # Разрешаем все типы обновлений
        )
        logger.info("Бот успешно запущен")

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())