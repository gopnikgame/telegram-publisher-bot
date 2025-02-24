import logging
import signal
import sys
from pathlib import Path
from telegram.ext import Updater
from app.bot import setup_bot
from app.config import config
from app.utils import setup_logging

# Добавляем проверку .env файла
def check_env():
    logger = logging.getLogger(__name__)
    env_path = Path('/app/.env')
    
    if not env_path.exists():
        logger.error("Файл .env не найден в /app/.env")
        return False
        
    with open(env_path) as f:
        content = f.read()
        logger.info(f"Содержимое .env файла: {len(content)} байт")
        if 'BOT_TOKEN=' not in content:
            logger.error("BOT_TOKEN не найден в .env файле")
            return False
        if content.find('BOT_TOKEN=') + 9 >= len(content) or not content[content.find('BOT_TOKEN=') + 9:].strip():
            logger.error("BOT_TOKEN пустой в .env файле")
            return False
    return True

def main():
    # Настраиваем логирование
    logger = setup_logging()
    
    try:
        # Проверяем .env файл
        if not check_env():
            sys.exit(1)
            
        # Проверяем токен
        if not config.BOT_TOKEN:
            logger.error("BOT_TOKEN не установлен в .env файле")
            sys.exit(1)

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
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()