import logging
import re

logger = logging.getLogger(__name__)  # Получаем логгер

def format_modern(text: str) -> str:
    """
    Форматирует текст в стиле modern (Discord-подобный).
    :param text: Исходный текст.
    :return: Отформатированный текст.
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    # 1. Сначала обрабатываем имеющиеся форматы
    # Сохраняем форматированные блоки и заменяем их плейсхолдерами
    placeholders = {}
    placeholder_id = 0

    # Регулярное выражение для поиска форматирования
    format_patterns = [
        (r'\*\*(.*?)\*\*', '*{}*'),  # **жирный** -> *жирный*
        (r'__(.*?)__', '_{}_'),  # __подчеркнутый__ -> _подчеркнутый_
        (r'\*(.*?)\*', '*{}*'),  # *курсив* -> *курсив*
        (r'_(.*?)_', '_{}_'),  # _курсив_ -> _курсив_
        (r'~~(.*?)~~', '~{}~'),  # ~~зачеркнутый~~ -> ~зачеркнутый~
        (r'`(.*?)`', '`{}`')  # `код` -> `код`
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

    return processed_text