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


def markdown_to_telegram_html(text: str) -> str:
    """
    Преобразует текст в формате Markdown в HTML, поддерживаемый Telegram.
    :param text: Исходный текст в формате Markdown.
    :return: Отформатированный текст в HTML, совместимый с Telegram.
    """
    try:
        if not text:
            return ""

        # Шаг 1: Экранируем HTML-специальные символы, кроме уже существующих HTML-тегов
        def escape_html_except_tags(match):
            content = match.group(1)
            return f"<{html.escape(match.group(2))}>{html.escape(content)}</{html.escape(match.group(2))}>"

        # Экранируем всё, кроме содержимого внутри HTML-тегов
        text = re.sub(r"<(.*?)>(.*?)</\1>", escape_html_except_tags, text)
        text = html.escape(text)

        # Шаг 2: Заменяем Markdown-разметку на поддерживаемые HTML-теги

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

        # Шаг 3: Обработка неподдерживаемых элементов

        # Заголовки # заголовок -> Текст с символом #
        text = re.sub(r'^(\#{1,6})\s(.*)$', r'\1 \2\n\n', text, flags=re.MULTILINE)

        # Цитаты >цитата -> Текст с символом >
        text = re.sub(r'^>\s?(.*)$', r'> \1\n', text, flags=re.MULTILINE)

        # Ненумерованные списки - пункт -> Текст с отступом
        text = re.sub(r'^([-*])\s(.*)$', r'• \2\n', text, flags=re.MULTILINE)

        # Нумерованные списки 1. пункт -> Текст с номером
        text = re.sub(r'^(\d+)\.\s(.*)$', r'\1. \2\n', text, flags=re.MULTILINE)

        # Горизонтальные линии *** -> Два переноса строки
        text = re.sub(r'^[\*\-\_]{3,}$', '\n\n', text, flags=re.MULTILINE)

        # Шаг 4: Удаляем лишние пробелы и нормализуем переносы строк
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)  # Сжимаем множественные переносы строк

        return text

    except Exception as e:
        logger.error(f"Ошибка преобразования Markdown в HTML для Telegram: {e}")
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