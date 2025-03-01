import logging
import html  # Для экранирования HTML
import re

from .markdown import (
    process_markdown_lists, process_markdown_code_blocks, process_markdown_tables, 
    process_emoji, process_headers, process_quotes, process_horizontal_rules,
    extract_and_save_placeholders, restore_placeholders
)

logger = logging.getLogger(__name__)  # Получаем логгер

def is_html_formatted(text: str) -> bool:
    """Проверяет, содержит ли текст HTML-теги."""
    html_tags_pattern = re.compile(r'<(/?)(strong|b|i|em|u|del|s|strike|code|pre|a|br|p|ul|ol|li|blockquote)(\s+[^>]*)?>')
    return bool(html_tags_pattern.search(text))

def format_html(text: str) -> str:
    """Форматирует текст в HTML."""
    if is_html_formatted(text):
        logger.info("Обнаружена HTML-разметка, пропускаем экранирование")  # Если текст уже содержит HTML-теги, не экранируем его
    else:
        logger.info("Конвертируем разметку в HTML")  # Конвертируем markdown-подобную разметку в HTML
        text = html.escape(text)  # Экранируем специальные символы сначала
        logger.info(f"Текст после экранирования HTML: {text[:100]}...")
        text = process_emoji(text)  # Обработка эмодзи
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)  # ***жирный курсив*** -> <strong><em>жирный курсив</em></strong>
        logger.info(f"После обработки супержирного: {text[:100]}...")
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # **жирный** -> <strong>жирный</strong>
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)  # ~~зачеркнутый~~ -> <del>зачеркнутый</del>
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # __подчеркнутый__ -> <u>подчеркнутый</u>
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)  # _курсив_ -> <em>курсив</em>
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # *курсив* -> <em>курсив</em>
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # `код` -> <code>код</code>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)  # [текст](ссылка) -> <a href="ссылка">текст</a>
        text = process_markdown_lists(text)  # Дополнительная обработка специальных элементов из модуля markdown
        text = process_markdown_tables(text)
        text = process_quotes(text)
        text = process_headers(text)
        text = process_horizontal_rules(text)
    return text

def markdown_to_html(text: str) -> str:
    """Преобразует текст в формате Markdown в HTML, поддерживаемый Telegram."""
    try:
        if not text:
            return ""
        logger.info("Начало конвертации Markdown в HTML")
        logger.info(f"Исходный текст Markdown: {text[:100]}...")
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')  # Шаг 1: Сохраняем блоки кода, чтобы не обрабатывать их содержимое
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')  # Шаг 2: Сохраняем inline код
        text = html.escape(text)  # Шаг 3: Экранируем HTML-специальные символы
        logger.info(f"После экранирования HTML: {text[:100]}...")
        text = process_emoji(text)  # Шаг 4: Обрабатываем эмодзи
        text = process_markdown_tables(text)  # Шаг 5: Обрабатываем таблицы
        text = process_markdown_lists(text)  # Шаг 6: Обрабатываем списки
        text = process_headers(text)  # Шаг 7: Обработка заголовков
        text = process_quotes(text)  # Шаг 8: Обработка цитат
        text = process_horizontal_rules(text)  # Шаг 9: Обработка горизонтальных линий
        logger.info(f"Текст перед обработкой форматирования: {text[:100]}...")  # Шаг 10: Заменяем Markdown-разметку на поддерживаемые HTML-теги
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)  # Супержирный текст ***текст*** -> <strong><em>текст</em></strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Жирный текст **текст** -> <strong>текст</strong>
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)  # Зачёркнутый текст ~~текст~~ -> <del>текст</del>
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # Подчёркнутый текст __текст__ -> <u>текст</u>
        text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<em>\1</em>', text)  # Курсив *текст* -> <em>текст</em>
        text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<em>\1</em>', text)  # Курсив _текст_ -> <em>текст</em>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)  # Ссылки [текст](ссылка) -> <a href="ссылка">текст</a>
        logger.info(f"После всей обработки форматирования: {text[:100]}...")
        for placeholder, code in inline_code.items():  # Шаг 11: Восстанавливаем inline код с преобразованием в HTML
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
        for placeholder, code_block in code_blocks.items():  # Шаг 12: Восстанавливаем блоки кода с преобразованием в HTML
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)  # Извлекаем язык и содержимое блока кода
            if match:
                language = match.group(1).strip()
                code_content = match.group(2)
                html_code_block = f'<pre><code class="{language}">{html.escape(code_content)}</code></pre>'
                text = text.replace(placeholder, html_code_block)
        text = text.strip()  # Шаг 13: Удаляем лишние пробелы и нормализуем переносы строк
        text = re.sub(r'\n{3,}', '\n\n', text)  # Сжимаем множественные переносы строк
        logger.info("Конвертация Markdown в HTML завершена")
        return text
    except Exception as e:
        logger.error(f"Ошибка преобразования Markdown в HTML для Telegram: {e}", exc_info=True)
        return text

def modern_to_html(text: str) -> str:
    """Преобразует текст в формате Modern в HTML, поддерживаемый Telegram."""
    try:
        logger.info("Начало конвертации Modern в HTML")
        logger.info(f"Исходный текст Modern: {text[:100]}...")
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')  # Шаг 1: Сохраняем блоки кода и inline код
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        text = html.escape(text)  # Шаг 2: Экранируем HTML-специальные символы
        text = process_emoji(text)  # Шаг 3: Обрабатываем эмодзи
        logger.info(f"Перед обработкой форматирования Modern: {text[:100]}...")  # Шаг 4: Заменяем Modern-разметку на HTML-теги
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)  # Жирный курсив ***текст*** -> <strong><em>текст</em></strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Жирный **текст** -> <strong>текст</strong>
        logger.info(f"После обработки жирного Modern: {text[:100]}...")
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)  # Зачеркнутый ~~текст~~ -> <del>текст</del>
        logger.info(f"После обработки зачеркнутого Modern: {text[:100]}...")
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)  # Подчеркнутый __текст__ -> <u>текст</u>
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)  # Курсив _текст_ -> <em>текст</em>
        text = re.sub(r'~(.*?)~', r'<del>\1</del>', text)  # Также поддерживаем зачеркнутый ~текст~ (один символ ~ в Modern)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)  # Ссылки [текст](ссылка) -> <a href="ссылка">текст</a>
        logger.info(f"После всей обработки форматирования Modern: {text[:100]}...")
        text = process_markdown_lists(text)  # Шаг 5: Обработка специальных элементов форматирования
        text = process_quotes(text)
        text = process_headers(text)
        for placeholder, code in inline_code.items():  # Шаг 6: Восстанавливаем код
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
        for placeholder, code_block in code_blocks.items():
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)
            if match:
                language = match.group(1).strip() or "code"
                code_content = match.group(2)
                html_code_block = f'<pre><code class="{language}">{html.escape(code_content)}</code></pre>'
                text = text.replace(placeholder, html_code_block)
        text = text.strip()  # Шаг 7: Форматирование текста
        if not text.endswith("\n\n"):
            text += "\n\n"
        logger.info("Конвертация Modern в HTML завершена")
        return text
    except Exception as e:
        logger.error(f"Ошибка преобразования Modern в HTML: {e}", exc_info=True)
        return text