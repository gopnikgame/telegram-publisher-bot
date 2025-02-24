import logging
import signal
import sys
import os
from datetime import datetime
from telegram.ext import Updater
from app.bot import setup_bot
from app.config import config
from app.utils import setup_logging

# Глобальные переменные
updater = None
START_TIME = datetime.utcnow()
CREATED_BY = os.getenv('CREATED_BY', 'unknown')
CREATED_AT = os.getenv('CREATED_AT', datetime.utcnow().strftime('%Y-%m-%d_%H:%M'))

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения работы."""
    logger = logging.getLogger(__name__)
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    
    if updater:
        logger.info("Останавливаем бота...")
        try:
            updater.stop()
            updater.is_idle = False
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")
    
    sys.exit(0)

def setup_signal_handlers():
    """Настройка обработчиков сигналов."""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Игнорируем SIGPIPE
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

def write_pid():
    """Запись PID процесса."""
    try:
        with open('/app/logs/bot.pid', 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"Ошибка при записи PID: {e}")

def main():
    global updater
    
    # Настраиваем логирование
    logger = setup_logging()
    
    try:
        # Записываем информацию о запуске
        logger.info(f"Bot started by {CREATED_BY} at {CREATED_AT}")
        logger.info(f"Current UTC time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Устанавливаем обработчики сигналов
        setup_signal_handlers()
        
        # Записываем PID
        write_pid()
        
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
    finally:
        # Очистка при выходе
        try:
            if os.path.exists('/app/logs/bot.pid'):
                os.remove('/app/logs/bot.pid')
        except Exception as e:
            logger.error(f"Ошибка при очистке PID файла: {e}")

if __name__ == '__main__':
    main()