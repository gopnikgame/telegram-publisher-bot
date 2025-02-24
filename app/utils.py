import logging
import os
import re
from datetime import datetime
from typing import List, Optional
from logging.handlers import RotatingFileHandler

class MessageFormattingError(Exception):
    """Ошибка форматирования сообщения"""
    pass

class FileSizeError(Exception):
    """Ошибка размера файла"""
    pass

def setup_logging():
    """Расширенная настройка логирования с ротацией файлов."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Основной файл лога
    main_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # Форматирование
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # Настройка логгера
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)
    logger.addHandler(logging.StreamHandler())
    
    return logger

def escape_markdown(text: str, version: int = 1) -> str:
    """
    Экранирование специальных символов для Markdown.
    
    Args:
        text (str): Текст для экранирования
        version (int): Версия Markdown (1 или 2)
        
    Returns:
        str: Экранированный текст
    """
    if version == 2:
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    else:
        escape_chars = ['_', '*', '`', '[']
    
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def extract_urls(text: str) -> List[str]:
    """
    Извлекает URL из текста.
    
    Args:
        text (str): Текст для анализа
        
    Returns:
        List[str]: Список найденных URL
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def format_links_inline(urls: List[str], format_type: str = 'markdown') -> str:
    """
    Форматирование ссылок с поддержкой разных форматов.
    
    Args:
        urls (List[str]): Список URL для форматирования
        format_type (str): Тип форматирования ('markdown', 'html', 'plain', 'modern')
        
    Returns:
        str: Отформатированный текст со ссылками
    """
    if not urls:
        return ''
    
    links = []
    for i, url in enumerate(urls, 1):
        if format_type == 'html':
            links.append(f'<a href="{url}">Ссылка {i}</a>')
        elif format_type == 'plain':
            links.append(f'Ссылка {i}: {url}')
        elif format_type == 'modern':
            escaped_url = escape_markdown(url, version=2)
            links.append(f"[Ссылка {i}]({escaped_url})")
        else:  # markdown
            escaped_url = escape_markdown(url, version=1)
            links.append(f"[Ссылка {i}]({escaped_url})")
    
    return "\n\n" + " | ".join(links)

def format_message(text: str, format_type: str = 'markdown') -> str:
    """
    Форматирование сообщения перед отправкой.
    
    Args:
        text (str): Исходный текст
        format_type (str): Тип форматирования ('markdown', 'html', 'plain', 'modern')
        
    Returns:
        str: Отформатированный текст
        
    Raises:
        MessageFormattingError: При ошибке форматирования
    """
    try:
        if text is None:
            return ''
        
        text = text.strip()
        urls = extract_urls(text)
        
        if format_type == 'plain':
            # Для обычного текста удаляем markdown разметку
            text = text.replace('**', '')
            text = re.sub(r'\s+', ' ', text)
            if urls:
                text += '\n\n' + format_links_inline(urls, 'plain')
            return text.strip()
            
        if format_type == 'html':
            # Для HTML заменяем markdown на HTML теги
            parts = text.split('**')
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Текст вне тегов
                    formatted_parts.append(part)
                else:  # Текст внутри тегов
                    formatted_parts.append(f"<b>{part}</b>")
            text = ''.join(formatted_parts)
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            for url in urls:
                text = text.replace(url, '')
            if urls:
                text += format_links_inline(urls, 'html')
            return text.strip()
            
        # Markdown и Modern форматирование
        for url in urls:
            text = text.replace(url, '')
        
        if format_type == 'modern':
            # Modern Markdown (v2)
            parts = text.split('**')
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Текст вне жирной разметки
                    formatted_parts.append(escape_markdown(part, version=2))
                else:  # Текст внутри жирной разметки
                    formatted_parts.append(f"*{escape_markdown(part, version=2)}*")
            text = ''.join(formatted_parts)
        else:
            # Обычный Markdown (v1)
            parts = text.split('**')
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Текст вне жирной разметки
                    formatted_parts.append(escape_markdown(part, version=1))
                else:  # Текст внутри жирной разметки
                    formatted_parts.append(f"*{escape_markdown(part, version=1)}*")
            text = ''.join(formatted_parts)
        
        # Общие правила форматирования
        text = re.sub(r'(\d+\.)(?=\S)', r'\1 ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\n\s+', '\n', text)
        
        if urls:
            text += format_links_inline(urls, format_type)
        
        return text.strip()
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка форматирования сообщения: {e}")
        raise MessageFormattingError(f"Не удалось отформатировать сообщение: {str(e)}")

def check_file_size(size: int, max_size: Optional[int] = None) -> bool:
    """
    Проверка размера файла.
    
    Args:
        size (int): Размер файла в байтах
        max_size (Optional[int]): Максимально допустимый размер
        
    Returns:
        bool: True если размер в пределах нормы
        
    Raises:
        FileSizeError: Если размер превышает лимит
    """
    from app.config import config
    limit = max_size or config.MAX_FILE_SIZE
    if size > limit:
        raise FileSizeError(f"Размер файла ({size} байт) превышает допустимый предел ({limit} байт)")
    return True

def format_bot_links(format_type: str = 'markdown') -> str:
    """
    Форматирование ссылок для ботов и каналов.
    
    Args:
        format_type (str): Тип форматирования ('markdown', 'html', 'plain', 'modern')
        
    Returns:
        str: Отформатированный текст со ссылками
    """
    from app.config import config
    
    links = []
    if config.MAIN_BOT_LINK and config.MAIN_BOT_NAME:
        if format_type == 'html':
            links.append(f'<a href="{config.MAIN_BOT_LINK}">{config.MAIN_BOT_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{config.MAIN_BOT_NAME}: {config.MAIN_BOT_LINK}')
        elif format_type == 'modern':
            links.append(f"[{escape_markdown(config.MAIN_BOT_NAME, 2)}]({escape_markdown(config.MAIN_BOT_LINK, 2)})")
        else:
            links.append(f"[{escape_markdown(config.MAIN_BOT_NAME)}]({escape_markdown(config.MAIN_BOT_LINK)})")
            
    if config.SUPPORT_BOT_LINK and config.SUPPORT_BOT_NAME:
        if format_type == 'html':
            links.append(f'<a href="{config.SUPPORT_BOT_LINK}">{config.SUPPORT_BOT_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{config.SUPPORT_BOT_NAME}: {config.SUPPORT_BOT_LINK}')
        elif format_type == 'modern':
            links.append(f"[{escape_markdown(config.SUPPORT_BOT_NAME, 2)}]({escape_markdown(config.SUPPORT_BOT_LINK, 2)})")
        else:
            links.append(f"[{escape_markdown(config.SUPPORT_BOT_NAME)}]({escape_markdown(config.SUPPORT_BOT_LINK)})")
            
    if config.CHANNEL_LINK and config.CHANNEL_NAME:
        if format_type == 'html':
            links.append(f'<a href="{config.CHANNEL_LINK}">{config.CHANNEL_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{config.CHANNEL_NAME}: {config.CHANNEL_LINK}')
        elif format_type == 'modern':
            links.append(f"[{escape_markdown(config.CHANNEL_NAME, 2)}]({escape_markdown(config.CHANNEL_LINK, 2)})")
        else:
            links.append(f"[{escape_markdown(config.CHANNEL_NAME)}]({escape_markdown(config.CHANNEL_LINK)})")
    
    return ' | '.join(links) if links else "Не настроены"