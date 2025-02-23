import logging
import os
import re
from datetime import datetime
from typing import List, Tuple, Optional
from logging.handlers import RotatingFileHandler

# Пользовательские исключения
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
        backupCount=5
    )
    
    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=1024 * 1024,
        backupCount=3
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

def escape_markdown(text: str) -> str:
    """
    Экранирование специальных символов для Markdown.
    
    Args:
        text (str): Исходный текст
        
    Returns:
        str: Текст с экранированными символами
    """
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def extract_urls(text: str) -> List[str]:
    """
    Извлекает URL из текста.
    
    Args:
        text (str): Исходный текст
        
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
        str: Отформатированные ссылки
    """
    if not urls:
        return ''
    
    links = []
    for i, url in enumerate(urls, 1):
        if format_type == 'html':
            links.append(f'<a href="{url}">Ссылка {i}</a>')
        elif format_type == 'plain':
            links.append(f'Ссылка {i}: {url}')
        else:  # markdown/modern
            escaped_url = escape_markdown(url)
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
            # Для обычного текста просто очищаем лишние пробелы
            text = re.sub(r'\s+', ' ', text)
            if urls:
                text += '\n\n' + format_links_inline(urls, 'plain')
            return text.strip()
            
        if format_type == 'html':
            # Экранирование HTML
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Форматирование ссылок для HTML
            for url in urls:
                text = text.replace(url, '')
            # Добавляем ссылки в конце
            if urls:
                text += format_links_inline(urls, 'html')
            return text.strip()
            
        # Markdown и Modern форматирование
        # Сначала удаляем URL из текста
        for url in urls:
            text = text.replace(url, '')
        
        if format_type == 'modern':
            # Сохраняем modern-форматирование (**жирный**)
            text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
        
        # Экранируем markdown
        text = escape_markdown(text)
        
        # Форматируем списки
        text = re.sub(r'(\d+\.)(?=\S)', r'\1 ', text)
        
        # Исправляем переносы строк
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\n\s+', '\n', text)
        
        # Добавляем ссылки в конце
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
        max_size (Optional[int]): Максимальный размер (если не указан, берется из Config)
        
    Returns:
        bool: True если размер допустимый, False иначе
        
    Raises:
        FileSizeError: При превышении допустимого размера
    """
    from app.config import Config
    limit = max_size or Config.MAX_FILE_SIZE
    if size > limit:
        raise FileSizeError(f"Размер файла ({size} байт) превышает допустимый предел ({limit} байт)")
    return True

def format_bot_links(format_type: str = 'markdown') -> str:
    """
    Форматирование ссылок для ботов и каналов.
    
    Args:
        format_type (str): Тип форматирования ('markdown', 'html', 'plain', 'modern')
        
    Returns:
        str: Отформатированные ссылки
    """
    from app.config import Config
    
    links = []
    if Config.MAIN_BOT_LINK and Config.MAIN_BOT_NAME:
        if format_type == 'html':
            links.append(f'<a href="{Config.MAIN_BOT_LINK}">{Config.MAIN_BOT_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{Config.MAIN_BOT_NAME}: {Config.MAIN_BOT_LINK}')
        else:
            links.append(f"[{escape_markdown(Config.MAIN_BOT_NAME)}]({escape_markdown(Config.MAIN_BOT_LINK)})")
            
    if Config.SUPPORT_BOT_LINK and Config.SUPPORT_BOT_NAME:
        if format_type == 'html':
            links.append(f'<a href="{Config.SUPPORT_BOT_LINK}">{Config.SUPPORT_BOT_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{Config.SUPPORT_BOT_NAME}: {Config.SUPPORT_BOT_LINK}')
        else:
            links.append(f"[{escape_markdown(Config.SUPPORT_BOT_NAME)}]({escape_markdown(Config.SUPPORT_BOT_LINK)})")
            
    if Config.CHANNEL_LINK and Config.CHANNEL_NAME:
        if format_type == 'html':
            links.append(f'<a href="{Config.CHANNEL_LINK}">{Config.CHANNEL_NAME}</a>')
        elif format_type == 'plain':
            links.append(f'{Config.CHANNEL_NAME}: {Config.CHANNEL_LINK}')
        else:
            links.append(f"[{escape_markdown(Config.CHANNEL_NAME)}]({escape_markdown(Config.CHANNEL_LINK)})")
    
    return ' | '.join(links) if links else "Не настроены"