import logging
import signal
import asyncio
from telegram.ext import Application
from app.bot import setup_handlers
from app.config import config
from app.utils import setup_logging

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

def setup_application():
    """Настройка приложения Telegram."""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в .env файле")
        return None

    # Создаем экземпляр Application
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .connect_timeout(30)  # Таймаут соединения
        .read_timeout(30)     # Таймаут чтения
        .get_updates_connect_timeout(30)  # Таймаут соединения для обновлений
        .get_updates_read_timeout(30)     # Таймаут чтения для обновлений
        .proxy(config.HTTPS_PROXY if config.HTTPS_PROXY else None)  # Прокси, если используется
        .build()
    )
    return application

async def run_bot(application):
    """Запуск бота."""
    try:
        # Инициализируем приложение
        await application.initialize()

        # Устанавливаем обработчики из bot.py
        setup_handlers(application)

        # Запуск бота
        logger.info("Бот запускается...")
        await application.start()
        await application.updater.start_polling()
        logger.info("Бот успешно запущен")

        # Ожидание завершения работы (замена idle())
        stop_signal = asyncio.Event()
        
        def signal_handler(sig, frame):
            logger.info("Получен сигнал остановки, завершаю работу...")
            stop_signal.set()
            
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Ожидаем сигнал завершения
        logger.info("Бот работает. Нажмите Ctrl+C для остановки")
        await stop_signal.wait()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)

    finally:
        # Останавливаем и завершаем работу бота
        if application.updater.running:
            await application.updater.stop()
        if application.running:
            await application.stop()
        await application.shutdown()

async def main() -> None:
    """Основная функция для запуска бота."""
    logger.info("Инициализация бота...")
    application = setup_application()
    if application:
        await run_bot(application)

if __name__ == "__main__":
    try:
        # Запускаем бота с помощью asyncio.run()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")