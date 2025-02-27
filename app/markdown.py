import logging
import re

logger = logging.getLogger(__name__)  # Получаем логгер

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