import logging
import os
from telegram import Message

def setup_logging():
    """Настройка логирования."""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Исправлено 'levellevelname' на 'levelname'
        level=logging.INFO,
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )

def escape_markdown(text: str) -> str:
    """Экранирование специальных символов для MarkdownV2."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', 
                   '{', '}', '.', '!']
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def check_file_size(message: Message) -> bool:
    """Проверка размера файла."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes

    if message.document:
        return message.document.file_size <= MAX_FILE_SIZE
    elif message.video:
        return message.video.file_size <= MAX_FILE_SIZE
    elif message.audio:
        return message.audio.file_size <= MAX_FILE_SIZE
    elif message.photo:
        return True  # Telegram автоматически сжимает фото
    return True