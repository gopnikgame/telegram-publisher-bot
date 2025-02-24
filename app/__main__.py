import logging
import sys
from telegram.ext import Updater
from app.bot import setup_bot
from app.config import config
from app.utils import setup_logging

def main():
    # Настраиваем логирование
    logger = setup_logging()
    
    try:
        # Проверяем токен
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN не установлен в .env файле")
            sys.exit(1)

        # Создаем updater с повышенными таймаутами
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
        
        # Используем polling с обработкой ошибок
        updater.start_polling(
            poll_interval=1.0,
            timeout=30,
            clean=True,
            bootstrap_retries=-1,
            drop_pending_updates=True
        )

        logger.info("Бот успешно запущен")
        
        # Запускаем бота до прерывания
        updater.idle()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()