import logging
from telegram.ext import Updater
from app.bot import setup_bot
from app.config import config
from app.utils import setup_logging

def main():
    # Настраиваем логирование
    logger = setup_logging()
    logger.info("Инициализация бота...")

    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле")
        return

    try:
        # Создаем updater
        updater = Updater(
            token=config.BOT_TOKEN,
            use_context=True,
            request_kwargs={
                'read_timeout': 30,
                'connect_timeout': 30,
                'proxy_url': config.HTTPS_PROXY if config.HTTPS_PROXY else None
            }
        )

        # Настраиваем бота
        setup_bot(updater.dispatcher)

        # Запускаем бота
        logger.info("Бот запускается...")
        updater.start_polling()

        logger.info("Бот успешно запущен")
        updater.idle()

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()