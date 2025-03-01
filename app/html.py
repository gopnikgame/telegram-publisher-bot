import logging
import html  # Для экранирования HTML
import re

from .markdown import (
    process_markdown_lists, 
    process_markdown_code_blocks, 
    process_markdown_tables, 
    process_emoji,
    process_headers,
    process_quotes,
    process_horizontal_rules,
    extract_and_save_placeholders,
    restore_placeholders
)

logger = logging.getLogger(__name__)  # Получаем логгер


def is_html_formatted(text: str) -> bool:
    """
    Проверяет, содержит ли текст HTML-теги.
    :param text: Проверяемый текст.
    :return: True, если текст содержит HTML-теги.
    """
    # Проверяем наличие распространенных HTML-тегов
    html_tags_pattern = re.compile(r'<(/?)(b|strong|i|em|u|s|strike|del|code|pre|a|br|p|ul|ol|li|blockquote)(\s+[^>]*)?>')
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
        # Заменяем разметку на HTML-теги
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)  # ***жирный курсив*** -> <b><i>жирный курсив</i></b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # **жирный** -> <b>жирный</b>
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # __подчеркнутый__ -> <u>подчеркнутый</u>
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)  # _курсив_ -> <i>курсив</i>
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)  # *курсив* -> <i>курсив</i>
        text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)  # ~~зачеркнутый~~ -> <s>зачеркнутый</s>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)  # [текст](ссылка) -> <a href="ссылка">текст</a>
    
        # Дополнительная обработка специальных элементов из модуля markdown
        text = process_emoji(text)
        text = process_markdown_lists(text)
        text = process_markdown_tables(text)
        text = process_quotes(text)
        text = process_headers(text)
        text = process_horizontal_rules(text)
    
    return text


def markdown_to_html(text: str) -> str:
    """
    Преобразует текст в формате Markdown в HTML, поддерживаемый Telegram.
    :param text: Исходный текст в формате Markdown.
    :return: Отформатированный текст в HTML, совместимый с Telegram.
    """
    try:
        if not text:
            return ""
        
        logger.info("Начало конвертации Markdown в HTML")
        
        # Шаг 1: Сохраняем блоки кода, чтобы не обрабатывать их содержимое
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')
        
        # Шаг 2: Сохраняем inline код
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        
        # Шаг 3: Экранируем HTML-специальные символы
        text = html.escape(text)
        
        # Шаг 4: Обрабатываем эмодзи
        text = process_emoji(text)
        
        # Шаг 5: Обрабатываем таблицы
        text = process_markdown_tables(text)
        
        # Шаг 6: Обрабатываем списки
        text = process_markdown_lists(text)
        
        # Шаг 7: Обработка заголовков
        text = process_headers(text)
        
        # Шаг 8: Обработка цитат
        text = process_quotes(text)
        
        # Шаг 9: Обработка горизонтальных линий
        text = process_horizontal_rules(text)
        
        # Шаг 10: Заменяем Markdown-разметку на поддерживаемые HTML-теги
        
        # Супержирный текст ***текст*** -> <b><i>текст</i></b>
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
        
        # Жирный текст **жирный** -> <b>жирный</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Подчёркнутый текст __подчёркнутый__ -> <u>подчёркнутый</u>
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
        
        # Курсив _курсив_ или *курсив* -> <i>курсив</i>
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)  # Улучшенное выражение для *курсив*
        text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<i>\1</i>', text)  # Улучшенное выражение для _курсив_
        
        # Зачёркнутый текст ~~зачёркнутый~~ -> <s>зачёркнутый</s>
        text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)
        
        # Ссылки [текст](ссылка) -> <a href="ссылка">текст</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # Шаг 11: Восстанавливаем inline код с преобразованием в HTML
        for placeholder, code in inline_code.items():
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
        
        # Шаг 12: Восстанавливаем блоки кода с преобразованием в HTML
        for placeholder, code_block in code_blocks.items():
            # Извлекаем язык и содержимое блока кода
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)
            if match:
                language = match.group(1).strip()
                code_content = match.group(2)
                
                html_code_block = f'<pre><code class="{language}">{html.escape(code_content)}</code></pre>'
                text = text.replace(placeholder, html_code_block)
        
        # Шаг 13: Удаляем лишние пробелы и нормализуем переносы строк
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)  # Сжимаем множественные переносы строк
        
        logger.info("Конвертация Markdown в HTML завершена")
        return text
        
    except Exception as e:
        logger.error(f"Ошибка преобразования Markdown в HTML для Telegram: {e}", exc_info=True)
        return text


def modern_to_html(text: str) -> str:
    """
    Преобразует текст в формате Modern в HTML, поддерживаемый Telegram.
    Формат Modern поддерживает также элементы Discord-подобной разметки.
    :param text: Исходный текст в формате Modern.
    :return: Отформатированный текст в HTML.
    """
    try:
        logger.info("Начало конвертации Modern в HTML")
        
        # Шаг 1: Сохраняем блоки кода и inline код
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        
        # Шаг 2: Экранируем HTML-специальные символы
        text = html.escape(text)
        
        # Шаг 3: Обрабатываем эмодзи
        text = process_emoji(text)
        
        # Шаг 4: Заменяем Modern-разметку на HTML-теги
        
        # Жирный курсив ***текст*** -> <b><i>текст</i></b>
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
        
        # Жирный **текст** -> <b>текст</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Подчеркнутый __текст__ -> <u>текст</u>
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
        
        # Курсив _текст_ -> <i>текст</i>
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # Зачеркнутый ~текст~ -> <s>текст</s> (один символ ~ в Modern)
        text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)
        
        # Ссылки [текст](ссылка) -> <a href="ссылка">текст</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        # Шаг 5: Обработка специальных элементов форматирования
        text = process_markdown_lists(text)  # Списки
        text = process_quotes(text)  # Цитаты
        text = process_headers(text)  # Заголовки
        
        # Шаг 6: Восстанавливаем код
        for placeholder, code in inline_code.items():
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
        
        for placeholder, code_block in code_blocks.items():
            # Извлекаем язык и содержимое блока кода
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)
            if match:
                language = match.group(1).strip() or "code"
                code_content = match.group(2)
                
                html_code_block = f'<pre><code class="{language}">{html.escape(code_content)}</code></pre>'
                text = text.replace(placeholder, html_code_block)
        
        # Шаг 7: Форматирование текста
        text = text.strip()
        if not text.endswith("\n\n"):
            text += "\n\n"
        
        logger.info("Конвертация Modern в HTML завершена")
        return text
        
    except Exception as e:
        logger.error(f"Ошибка преобразования Modern в HTML: {e}", exc_info=True)
        return text