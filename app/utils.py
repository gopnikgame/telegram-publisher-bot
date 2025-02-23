import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настройка логирования."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'bot.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger

def format_message(text):
    """Форматирование сообщения с добавлением ссылок."""
    formatted_text = f"{text}\n\n{Config.MAIN_BOT_LINK}\n{Config.SUPPORT_BOT_LINK}\n{Config.CHANNEL_LINK}"
    return formatted_text

def check_file_size(file_size):
    """Проверка размера файла."""
    return file_size <= Config.MAX_FILE_SIZE