import logging
import os
import re
from telegram import Message, ParseMode

def setup_logging():
    """Настройка логирования."""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )

def format_message(text: str, format_type: str) -> tuple:
    """
    Форматирование сообщения в зависимости от выбранного формата.
    Возвращает кортеж (отформатированный_текст, parse_mode)
    """
    if format_type == "modern":
        # Не экранируем эмодзи и хештеги
        return text, ParseMode.MARKDOWN
    elif format_type == "markdown":
        return escape_markdown(text), ParseMode.MARKDOWN_V2
    elif format_type == "html":
        return escape_html(text), ParseMode.HTML
    else:  # plain
        return text, None

def escape_markdown(text: str) -> str:
    """Экранирование специальных символов для MarkdownV2."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', 
                   '{', '}', '.', '!']
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def escape_html(text: str) -> str:
    """Экранирование специальных символов для HTML."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

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