import logging
import html  # Для экранирования HTML
import re

logger = logging.getLogger(__name__)  # Получаем логгер


def is_html_formatted(text: str) -> bool:
    """
    Проверяет, содержит ли текст HTML-теги.
    :param text: Проверяемый текст.
    :return: True, если текст содержит HTML-теги.
    """
    # Проверяем наличие распространенных HTML-тегов
    html_tags_pattern = re.compile(r'<(/?)(b|strong|i|em|u|s|strike|del|code|pre|a|br|p)(\s+[^>]*)?>')
    return bool(html_tags_pattern.search(text))


def format_html(text: str) -> str:
    """
    Форматирует текст в HTML.
    :param text: Исходный текст.
    :return: Отформатированный текст в HTML.
    """
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
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # __подчеркнутый__ -> <u>подчеркнутый</u>
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)  # _курсив_ -> <i>курсив</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)  # *курсив* -> <i>курсив</i>
        text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)  # ~~зачеркнутый~~ -> <s>зачеркнутый</s>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>
    return text


def markdown_to_html(text: str) -> str:
    """
    Преобразует текст в формате Markdown в HTML, поддерживаемый Telegram.
    :param text: Исходный текст в формате Markdown.
    :return: Отформатированный текст в HTML.
    """
    text = html.escape(text)  # Экранируем HTML-специальные символы

    # Заменяем Markdown-разметку на HTML-теги
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # **жирный** -> <b>жирный</b>
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # __подчеркнутый__ -> <u>подчеркнутый</u>
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)  # _курсив_ -> <i>курсив</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)  # *курсив* -> <i>курсив</i>
    text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)  # ~~зачеркнутый~~ -> <s>зачеркнутый</s>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>

    return text + "\n\n" #  Заменяем <br><br> на \n\n


def modern_to_html(text: str) -> str:
    """
    Преобразует текст в формате Modern в HTML, поддерживаемый Telegram.
    :param text: Исходный текст в формате Modern.
    :return: Отформатированный текст в HTML.
    """
    text = html.escape(text)  # Экранируем HTML-специальные символы

    # Заменяем Modern-разметку на HTML-теги (примерно так же, как и Markdown)
    text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)  # *жирный* -> <b>жирный</b>
    text = re.sub(r'_(.*?)_', r'<u>\1</u>', text)  # _подчеркнутый_ -> <u>подчеркнутый</u>
    text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)  # ~зачеркнутый~ -> <s>зачеркнутый</s>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>

    return text + "\n\n" #  Заменяем <br><br> на \n\n