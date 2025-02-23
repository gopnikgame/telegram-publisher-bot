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

def format_message(text):
    """Форматирование сообщения перед отправкой."""
    if text is None:
        return ''
    
    text = text.strip()
    
    # Конвертация Modern/Discord формата в Markdown
    # Заменяем **текст** на *текст* для жирного начертания
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # Обработка эмодзи - оставляем как есть
    # Обработка списков - добавляем пробел после точки если его нет
    text = re.sub(r'(\d+\.)(?=\S)', r'\1 ', text)
    
    # Исправляем множественные переносы строк
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def check_file_size(size):
    """Проверка размера файла."""
    from app.config import Config
    return size <= Config.MAX_FILE_SIZE