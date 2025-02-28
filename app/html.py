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
    try:
        if not text:
            return ""

        # Экранирование HTML
        def escape_html_except_tags(match):
            content = match.group(1)
            return f"<{html.escape(match.group(2))}>{html.escape(content)}</{html.escape(match.group(2))}>"
        text = re.sub(r"<(.*?)>(.*?)</\1>", escape_html_except_tags, text)
        text = html.escape(text)

        # Супержирный текст ***текст*** -> <b><i>текст</i></b>
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)

        # Жирный текст **жирный** -> <b>жирный</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

        # Подчёркнутый текст __подчёркнутый__ -> <u>подчёркнутый</u>
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)

        # Курсив _курсив_ или *курсив* -> <i>курсив</i>
        text = re.sub(r'[_*](.*?)[_*]', r'<i>\1</i>', text)

        # Зачёркнутый текст ~~зачёркнутый~~ -> <s>зачёркнутый</s>
        text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)

        # Код `код` -> <code>код</code>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

        # Ссылки [текст](ссылка) -> <a href="ссылка">текст</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

        # Цитаты >цитата -> <blockquote>цитата</blockquote>
        text = re.sub(r'^>\s?(.*)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)

        # Ненумерованные списки - пункт -> <ul><li>пункт</li></ul>
        text = re.sub(r'^([-*])\s(.*)$', r'<ul><li>\2</li></ul>', text, flags=re.MULTILINE)

        # Нумерованные списки 1. пункт -> <ol><li>пункт</li></ol>
        text = re.sub(r'^(\d+)\.\s(.*)$', r'<ol><li>\2</li></ol>', text, flags=re.MULTILINE)

        # Заголовки # заголовок -> <h1>заголовок</h1>
        for i in range(1, 7):
            text = re.sub(rf'^{"#" * i}\s(.*)$', rf'<h{i}>\1</h{i}>', text, flags=re.MULTILINE)

        # Горизонтальные линии *** -> <hr>
        text = re.sub(r'^[\*\-\_]{3,}$', '<hr>', text, flags=re.MULTILINE)

        # Нормализация переносов строк
        text = text.strip()
        text = re.sub(r'\n{2,}', '\n\n', text)

        return text

    except Exception as e:
        logger.error(f"Ошибка преобразования Markdown в HTML: {e}")
        return text

def modern_to_html(text: str) -> str:
    """
    Преобразует текст в формате Modern в HTML, поддерживаемый Telegram.
    :param text: Исходный текст в формате Modern.
    :return: Отформатированный текст в HTML.
    """
    try:
        text = html.escape(text)  # Экранируем HTML-специальные символы

        # Заменяем Modern-разметку на HTML-теги
        text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)  # *жирный* -> <b>жирный</b>
        text = re.sub(r'_(.*?)_', r'<u>\1</u>', text)  # _подчеркнутый_ -> <u>подчеркнутый</u>
        text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)  # ~зачеркнутый~ -> <s>зачеркнутый</s>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>

        # Удаляем лишние пробелы и добавляем \n\n, если необходимо
        text = text.strip() + "\n\n" if not text.endswith("\n\n") else text
        return text
    except Exception as e:
        logger.error(f"Ошибка преобразования Modern в HTML: {e}")
        return text