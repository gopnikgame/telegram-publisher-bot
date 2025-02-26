import logging
import os
import re
from datetime import datetime
from typing import List, Optional
from logging.handlers import RotatingFileHandler
import html  # Для экранирования HTML

class MessageFormattingError(Exception):
    """Ошибка форматирования сообщения."""
    pass


class FileSizeError(Exception):
    """Ошибка размера файла."""
    pass


def setup_logging():
    """
    Настройка логирования с ротацией файлов.
    Создает два файла: основной лог и лог ошибок.
    """
    log_dir = '/opt/telegram-publisher-bot/logs'  # Используем абсолютный путь
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Основной файл лога
    main_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bot.log'),
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        encoding='utf-8'
    )

    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    # Форматирование
    formatter = logging.Formatter(
        '%Y-%m-%d %H:%M:%S - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Настройка логгера
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)
    logger.addHandler(logging.StreamHandler())  # Вывод в консоль

    return logger


def format_bot_links(format_type: str = 'markdown') -> str:
    """
    Форматирование ссылок ботов и канала.
    :param format_type: Тип форматирования (markdown, html, plain).
    """
    from app.config import config

    links = []

    def format_link(name: str, url: str, format_type: str) -> str:
        if format_type == 'html':
            name = html.escape(name)
            url = html.escape(url)
            return f'<a href="{url}">{name}</a>'
        elif format_type == 'plain':
            return f'{name}: {url}'
        else:  # markdown и modern
            return f"[{name}]({url})"

    # Добавляем ссылки только если они настроены
    if config.MAIN_BOT_LINK и config.MAIN_BOT_NAME:
        links.append(format_link(config.MAIN_BOT_NAME, config.MAIN_BOT_LINK, format_type))
    if config.SUPPORT_BOT_LINK и config.SUPPORT_BOT_NAME:
        links.append(format_link(config.SUPPORT_BOT_NAME, config.SUPPORT_BOT_LINK, format_type))
    if config.CHANNEL_LINK и config.CHANNEL_NAME:
        links.append(format_link(config.CHANNEL_NAME, config.CHANNEL_LINK, format_type))

    return ' | '.join(links) if links else ""


def append_links_to_message(text: str, format_type: str = 'markdown') -> str:
    """
    Добавляет отформатированные ссылки к сообщению.
    :param text: Исходное сообщение.
    :param format_type: Тип форматирования.
    """
    links = format_bot_links(format_type)
    if links:
        return f"{text}\n\n{links}"
    return text


def format_message(text: str, format_type: str = 'markdown') -> str:
    """
    Форматирование сообщения с поддержкой разных форматов.
    :param text: Исходный текст.
    :param format_type: Тип форматирования (markdown, html, plain, modern).
    """
    logger = logging.getLogger(__name__)  # Получаем логгер

    try:
        if not text:
            return ''

        text = text.strip()

        if format_type == 'plain':
            # Убираем разметку
            text = text.replace('**', '')
            return append_links_to_message(text, format_type)

        if format_type == 'html':
            # Экранируем HTML
            text = html.escape(text)
            return append_links_to_message(text, format_type)

        # Для markdown и modern
        if format_type == 'modern':
            # Экранируем специальные символы для MarkdownV2
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
        else:
            # Экранируем только основные символы для обычного Markdown
            special_chars = ['[', ']', '(', ')', '`']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')

        # Обработка жирного текста
        if '**' in text:
            parts = text.split('**')
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Обычный текст
                    formatted_parts.append(part)
                else:  # Жирный текст
                    formatted_parts.append(f"*{part}*")
            text = ''.join(formatted_parts)

        return append_links_to_message(text, format_type)

    except Exception as e:
        logger.error(f"Ошибка форматирования сообщения: {e}")
        raise MessageFormattingError(f"Ошибка форматирования: {str(e)}")


def check_file_size(size: int, max_size: Optional[int] = None) -> bool:
    """
    Проверка размера файла.
    :param size: Размер файла в байтах.
    :param max_size: Максимальный допустимый размер файла (опционально).
    """
    from app.config import config

    limit = max_size or config.MAX_FILE_SIZE
    if size > limit:
        raise FileSizeError(f"Размер файла ({size} байт) превышает лимит ({limit} байт)")
    return True