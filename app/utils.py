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
    # Список специальных символов, которые нужно экранировать в Markdown V2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # Замена всех спец. символов на экранированные версии
    for char in escape_chars:
        # Проверка, не экранирован ли уже символ
        text = re.sub(r'(?<!\\)' + re.escape(char), r'\\' + char, text)
    
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
            escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                # Проверка, не экранирован ли уже символ
                escaped_url = re.sub(r'(?<!\\)' + re.escape(char), r'\\' + char, escaped_url)
                escaped_name = re.sub(r'(?<!\\)' + re.escape(char), r'\\' + char, escaped_name)
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


def is_already_escaped(text: str, pos: int, char: str) -> bool:
    """
    Проверяет, экранирован ли уже символ в позиции pos.
    :param text: Текст для проверки
    :param pos: Позиция символа
    :param char: Сам символ
    :return: True, если символ уже экранирован
    """
    if pos > 0 and text[pos-1] == '\\':
        # Проверяем, чтобы этот обратный слеш не был экранированным сам
        return pos <= 1 or text[pos-2] != '\\'
    return False


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

        # Для markdown и modern режимов
        result = ""
        
        # Обработка форматирования
        # Простой подход: сначала экранируем все специальные символы
        # и затем обрабатываем форматирование
        
        # Список специальных символов для экранирования
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        # 1. Сначала обрабатываем имеющиеся форматы
        # Сохраняем форматированные блоки и заменяем их плейсхолдерами
        placeholders = {}
        placeholder_id = 0
        
        # Регулярное выражение для поиска форматирования
        format_patterns = [
            (r'\*\*(.*?)\*\*', '*{}*'),     # **жирный** -> *жирный*
            (r'__(.*?)__', '_{}_'),         # __подчеркнутый__ -> _подчеркнутый_
            (r'\*(.*?)\*', '*{}*'),         # *курсив* -> *курсив*
            (r'_(.*?)_', '_{}_'),           # _курсив_ -> _курсив_
            (r'~~(.*?)~~', '~{}~'),         # ~~зачеркнутый~~ -> ~зачеркнутый~
            (r'`(.*?)`', '`{}`')            # `код` -> `код`
        ]

        # Работаем с копией текста
        processed_text = text
        
        for pattern, format_template in format_patterns:
            # Находим все совпадения в тексте
            matches = list(re.finditer(pattern, processed_text))
            
            # Обрабатываем совпадения с конца, чтобы не нарушать индексы
            for match in reversed(matches):
                start, end = match.span()
                content = match.group(1)
                
                # Создаем плейсхолдер
                placeholder = f"__PLACEHOLDER_{placeholder_id}__"
                placeholder_id += 1
                
                # Экранируем содержимое форматированного блока
                escaped_content = content
                for char in special_chars:
                    escaped_content = re.sub(r'(?<!\\)' + re.escape(char), r'\\' + char, escaped_content)
                
                # Заменяем форматированный текст на плейсхолдер
                placeholders[placeholder] = format_template.format(escaped_content)
                processed_text = processed_text[:start] + placeholder + processed_text[end:]
        
        # 2. Экранируем все оставшиеся специальные символы
        for char in special_chars:
            processed_text = re.sub(r'(?<!\\)' + re.escape(char), r'\\' + char, processed_text)
        
        # 3. Восстанавливаем форматированные блоки
        for placeholder, formatted_text in placeholders.items():
            processed_text = processed_text.replace(placeholder, formatted_text)
        
        result = processed_text
        
        # Добавляем ссылки в конце сообщения
        return append_links_to_message(result, format_type)

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