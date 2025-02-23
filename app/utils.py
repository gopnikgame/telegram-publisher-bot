import logging
import os
import re
from datetime import datetime

def setup_logging():
    """Настройка логирования."""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def escape_markdown(text):
    """Экранирование специальных символов для Markdown."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join('\\' + char if char in escape_chars else char for char in text)

def extract_urls(text):
    """Извлекает URL из текста."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def format_links_inline(urls):
    """Форматирует ссылки в одну строку."""
    if not urls:
        return ''
    
    links = []
    for i, url in enumerate(urls, 1):
        # Экранируем специальные символы в URL
        escaped_url = escape_markdown(url)
        links.append(f"[Ссылка {i}]({escaped_url})")
    
    return "\n\n" + " | ".join(links)

def format_message(text):
    """Форматирование сообщения перед отправкой."""
    if text is None:
        return ''
    
    text = text.strip()
    
    # Сохраняем ссылки
    urls = extract_urls(text)
    
    # Удаляем URL из текста
    for url in urls:
        text = text.replace(url, '')
    
    # Экранируем специальные символы в тексте
    text = escape_markdown(text)
    
    # Конвертация Modern/Discord формата в Markdown
    text = re.sub(r'\\\*\\\*(.*?)\\\*\\\*', r'*\1*', text)
    
    # Обработка списков
    text = re.sub(r'(\d+\.)(?=\S)', r'\1 ', text)
    
    # Исправляем множественные переносы строк
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Очищаем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s+', '\n', text)
    
    # Добавляем ссылки в конце текста в одну строку
    if urls:
        text += format_links_inline(urls)
    
    return text.strip()

def check_file_size(size):
    """Проверка размера файла."""
    from app.config import Config
    return size <= Config.MAX_FILE_SIZE

def format_bot_links():
    """Форматирование ссылок для ботов и каналов."""
    from app.config import Config
    
    links = []
    if Config.MAIN_BOT_LINK and Config.MAIN_BOT_NAME:
        links.append(f"[{escape_markdown(Config.MAIN_BOT_NAME)}]({escape_markdown(Config.MAIN_BOT_LINK)})")
    if Config.SUPPORT_BOT_LINK and Config.SUPPORT_BOT_NAME:
        links.append(f"[{escape_markdown(Config.SUPPORT_BOT_NAME)}]({escape_markdown(Config.SUPPORT_BOT_LINK)})")
    if Config.CHANNEL_LINK and Config.CHANNEL_NAME:
        links.append(f"[{escape_markdown(Config.CHANNEL_NAME)}]({escape_markdown(Config.CHANNEL_LINK)})")
    
    return ' | '.join(links) if links else "Не настроены"