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


def escape_markdown_v2(text: str) -> str:
    """
    Экранирование специальных символов для MarkdownV2.
    :param text: Исходный текст.
    :return: Экранированный текст для MarkdownV2.
    """
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_bot_links(format_type: str = 'markdown') -> str:
    """
    Форматирование ссылок ботов и канала.
    :param format_type: Тип форматирования (markdown, html, plain, modern).
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
            # Экранируем специальные символы в URL и имени для MarkdownV2
            escaped_url = url
            escaped_name = name
            for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
                escaped_url = escaped_url.replace(char, f'\\{char}')
                escaped_name = escaped_name.replace(char, f'\\{char}')
            return f"[{escaped_name}]({escaped_url})"

    # Добавляем ссылки только если они настроены
    if config.MAIN_BOT_LINK and config.MAIN_BOT_NAME:
        links.append(format_link(config.MAIN_BOT_NAME, config.MAIN_BOT_LINK, format_type))
    if config.SUPPORT_BOT_LINK and config.SUPPORT_BOT_NAME:
        links.append(format_link(config.SUPPORT_BOT_NAME, config.SUPPORT_BOT_LINK, format_type))
    if config.CHANNEL_LINK and config.CHANNEL_NAME:
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


def is_html_formatted(text: str) -> bool:
    """
    Проверяет, содержит ли текст HTML-теги.
    :param text: Проверяемый текст.
    :return: True, если текст содержит HTML-теги.
    """
    # Проверяем наличие распространенных HTML-тегов
    html_tags_pattern = re.compile(r'<(/?)(b|strong|i|em|u|s|strike|del|code|pre|a|br|p)(\s+[^>]*)?>')
    return bool(html_tags_pattern.search(text))


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
            # Убираем всю разметку
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Убираем **жирный**
            text = re.sub(r'__(.*?)__', r'\1', text)      # Убираем __подчеркнутый__
            text = re.sub(r'_(.*?)_', r'\1', text)        # Убираем _курсив_
            text = re.sub(r'\*(.*?)\*', r'\1', text)      # Убираем *курсив*
            text = re.sub(r'~~(.*?)~~', r'\1', text)      # Убираем ~~зачеркнутый~~
            text = re.sub(r'`(.*?)`', r'\1', text)        # Убираем `код`
            return append_links_to_message(text, format_type)

        if format_type == 'html':
            # Проверяем, содержит ли текст уже HTML-разметку
            if is_html_formatted(text):
                # Если текст уже содержит HTML-теги, не экранируем его
                logger.info("Обнаружена HTML-разметка, пропускаем экранирование")
            else:
                # Конвертируем markdown-подобную разметку в HTML
                logger.info("Конвертируем разметку в HTML")
                # Экранируем специальные символы сначала
                text = html.escape(text)
                # Затем заменяем разметку на HTML-теги
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # **жирный** -> <b>жирный</b>
                text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)       # __подчеркнутый__ -> <u>подчеркнутый</u>
                text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)         # _курсив_ -> <i>курсив</i>
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)       # *курсив* -> <i>курсив</i>
                text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)       # ~~зачеркнутый~~ -> <s>зачеркнутый</s>
                text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)   # `код` -> <code>код</code>
            return append_links_to_message(text, format_type)

        # Для markdown и modern
        if format_type == 'modern':
            # Обработка современного Discord-подобного форматирования для MarkdownV2
            # Сохраняем текст с защитой форматирования
            pattern_map = {
                r'\*\*(.*?)\*\*': lambda m: f"*{escape_markdown_v2(m.group(1))}*",  # **жирный** -> *жирный*
                r'__(.*?)__': lambda m: f"__{escape_markdown_v2(m.group(1))}__",    # __подчеркнутый__ 
                r'_(.*?)_': lambda m: f"_{escape_markdown_v2(m.group(1))}_",        # _курсив_
                r'~~(.*?)~~': lambda m: f"~{escape_markdown_v2(m.group(1))}~",      # ~~зачеркнутый~~ -> ~зачеркнутый~
                r'`(.*?)`': lambda m: f"`{escape_markdown_v2(m.group(1))}`"         # `код`
            }
            
            # Временно заменяем форматирование на маркеры
            placeholder_map = {}
            placeholder_counter = 0
            
            # Находим и заменяем форматирование на уникальные маркеры
            for pattern in pattern_map.keys():
                matches = re.finditer(pattern, text)
                offset = 0  # Для корректировки позиций при замене
                for match in matches:
                    start, end = match.span()
                    start += offset
                    end += offset
                    placeholder = f"__PLACEHOLDER_{placeholder_counter}__"
                    placeholder_counter += 1
                    
                    # Сохраняем оригинальный текст и его форматирование
                    formatted_text = pattern_map[pattern](match)
                    placeholder_map[placeholder] = formatted_text
                    
                    # Заменяем оригинальный текст на маркер
                    text = text[:start] + placeholder + text[end:]
                    offset += len(placeholder) - (end - start)
            
            # Экранируем весь текст кроме маркеров
            text = escape_markdown_v2(text)
            
            # Восстанавливаем форматированный текст
            for placeholder, formatted_text in placeholder_map.items():
                text = text.replace(escape_markdown_v2(placeholder), formatted_text)
                
        else:  # обычный markdown
            # Преобразуем разметку Markdown в формат совместимый с MarkdownV2
            pattern_map = {
                r'\*\*(.*?)\*\*': lambda m: f"*{m.group(1)}*",        # **жирный** -> *жирный*
                r'__(.*?)__': lambda m: f"__{m.group(1)}__",           # __подчеркнутый__ 
                r'_(.*?)_': lambda m: f"_{m.group(1)}_",               # _курсив_
                r'\*(.*?)\*': lambda m: f"*{m.group(1)}*",             # *курсив*
                r'~~(.*?)~~': lambda m: f"~{m.group(1)}~",             # ~~зачеркнутый~~ -> ~зачеркнутый~
                r'`(.*?)`': lambda m: f"`{m.group(1)}`"                # `код`
            }
            
            # Подход похож на modern, но экранируем только специальные символы вне форматирования
            placeholder_map = {}
            placeholder_counter = 0
            
            # Находим и заменяем форматирование на уникальные маркеры
            for pattern in pattern_map.keys():
                matches = re.finditer(pattern, text)
                offset = 0
                for match in matches:
                    start, end = match.span()
                    start += offset
                    end += offset
                    placeholder = f"__PLACEHOLDER_{placeholder_counter}__"
                    placeholder_counter += 1
                    
                    # Сохраняем только содержимое внутри форматирования
                    inner_content = match.group(1)
                    formatted_text = pattern_map[pattern](match)
                    placeholder_map[placeholder] = formatted_text
                    
                    text = text[:start] + placeholder + text[end:]
                    offset += len(placeholder) - (end - start)
            
            # Экранируем только специальные символы, которые могут мешать парсингу Markdown
            escape_chars = ['[', ']', '(', ')', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                text = text.replace(char, f'\\{char}')
            
            # Восстанавливаем форматированный текст
            for placeholder, formatted_text in placeholder_map.items():
                # Восстанавливаем плейсхолдеры с учетом возможного экранирования
                escaped_placeholder = placeholder
                for char in escape_chars:
                    if char in placeholder:
                        escaped_placeholder = escaped_placeholder.replace(char, f'\\{char}')
                text = text.replace(escaped_placeholder, formatted_text)

        return append_links_to_message(text, format_type)

    except Exception as e:
        logger.error(f"Ошибка форматирования сообщения: {e}", exc_info=True)
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