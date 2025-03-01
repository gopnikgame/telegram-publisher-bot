import logging
import html  # Для экранирования HTML
import re

from .markdown import (
    process_emoji, process_headers, process_quotes, process_horizontal_rules,
    extract_and_save_placeholders, restore_placeholders,
    process_bold_text, process_italic_text, process_strikethrough_text,
    process_underline_text, process_bold_italic_text, process_links, process_code
)

logger = logging.getLogger(__name__)  # Получаем логгер

def is_html_formatted(text: str) -> bool:
    """Проверяет, содержит ли текст HTML-теги."""
    html_tags_pattern = re.compile(r'<(/?)(strong|b|i|em|u|del|s|strike|code|pre|a|br|p)(\s+[^>]*)?>')
    return bool(html_tags_pattern.search(text))

# Функция для простого форматирования списков в тексте
def format_simple_lists(text: str) -> str:
    """
    Преобразует списки в простой текстовый формат, поддерживаемый Telegram.
    """
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        # Нумерованный список: заменяем на простой текст с номером
        ordered_match = re.match(r'^\s*(\d+)[.)]\s+(.*)', line)
        if ordered_match:
            number = ordered_match.group(1)
            content = ordered_match.group(2)
            result.append(f"{number}. {content}")
            continue
            
        # Маркированный список: заменяем на простой текст с тире или точкой
        unordered_match = re.match(r'^\s*[-*+]\s+(.*)', line)
        if unordered_match:
            content = unordered_match.group(1)
            result.append(f"• {content}")
            continue
            
        result.append(line)
    
    return '\n'.join(result)

# Функция для простого форматирования таблиц в тексте
def format_simple_tables(text: str) -> str:
    """
    Преобразует markdown таблицы в простой текстовый формат.
    """
    lines = text.split('\n')
    result = []
    in_table = False
    table_data = []
    
    for i, line in enumerate(lines):
        # Проверяем, является ли строка частью таблицы
        if re.match(r'^\s*\|.*\|\s*$', line):
            in_table = True
            # Извлекаем ячейки, удаляя начальный и конечный разделитель
            cells = [cell.strip() for cell in line.strip('| \t').split('|')]
            table_data.append(cells)
        elif in_table:
            # Если это разделитель заголовка таблицы, пропускаем его
            if re.match(r'^\s*\|([-:]+\|)+\s*$', line):
                continue
            
            # Вышли из таблицы, форматируем собранные данные
            if table_data:
                result.append(format_table_as_text(table_data))
                table_data = []
            in_table = False
            result.append(line)
        else:
            result.append(line)
    
    # Обработка таблицы в конце текста
    if in_table and table_data:
        result.append(format_table_as_text(table_data))
    
    return '\n'.join(result)

def format_table_as_text(table_data):
    """
    Форматирует данные таблицы в виде простого текста.
    """
    if not table_data:
        return ""
    
    # Находим максимальную ширину для каждого столбца
    col_widths = [0] * len(table_data[0])
    for row in table_data:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))
    
    # Форматируем каждую строку таблицы
    formatted_rows = []
    for i, row in enumerate(table_data):
        formatted_cells = [cell.ljust(col_widths[j]) for j, cell in enumerate(row) if j < len(col_widths)]
        formatted_row = " | ".join(formatted_cells)
        formatted_rows.append(formatted_row)
        
        # Добавляем разделитель после заголовка
        if i == 0:
            separator = "-" * len(formatted_row)
            formatted_rows.append(separator)
    
    return '\n'.join(formatted_rows)

def format_html(text: str) -> str:
    """Форматирует текст в HTML."""
    if is_html_formatted(text):
        logger.info("Обнаружена HTML-разметка, пропускаем экранирование")
    else:
        logger.info("Конвертируем разметку в HTML")
        text = html.escape(text)
        logger.info(f"Текст после экранирования HTML: {text[:100]}...")
        
        # Сначала преобразуем списки и таблицы в простой текст
        text = format_simple_lists(text)
        text = format_simple_tables(text)
        
        # Применяем форматирование, поддерживаемое Telegram
        text = process_emoji(text)
        text = process_bold_italic_text(text)
        logger.info(f"После обработки супержирного: {text[:100]}...")
        text = process_bold_text(text)
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = process_strikethrough_text(text)
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = process_underline_text(text)
        text = process_italic_text(text)
        text = process_code(text)
        text = process_links(text)
        text = process_headers(text)
        
    return text

def markdown_to_html(text: str) -> str:
    """Преобразует текст в формате Markdown в HTML, поддерживаемый Telegram."""
    try:
        if not text:
            return ""
        logger.info("Начало конвертации Markdown в HTML")
        logger.info(f"Исходный текст Markdown: {text[:100]}...")
        
        # Шаг 1-2: Сохраняем блоки кода и inline код
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        
        # Шаг 3: Экранируем HTML-специальные символы
        text = html.escape(text)
        logger.info(f"После экранирования HTML: {text[:100]}...")
        
        # Обработка списков и таблиц в простой текстовый формат
        text = format_simple_lists(text)
        text = format_simple_tables(text)
        
        # Шаг 4-9: Базовая обработка Markdown
        text = process_emoji(text)
        text = process_headers(text)
        text = process_quotes(text)
        text = process_horizontal_rules(text)
        
        # Шаг 10: Базовое форматирование текста
        logger.info(f"Текст перед обработкой форматирования: {text[:100]}...")
        text = process_bold_italic_text(text)
        text = process_bold_text(text)
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = process_strikethrough_text(text)
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = process_underline_text(text)
        text = process_italic_text(text)
        text = process_links(text)
        logger.info(f"После всей обработки форматирования: {text[:100]}...")
        
        # Шаг 11-12: Восстанавливаем код
        for placeholder, code in inline_code.items():
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
            
        for placeholder, code_block in code_blocks.items():
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)
            if match:
                language = match.group(1).strip()
                code_content = match.group(2)
                html_code_block = f'<pre><code>{html.escape(code_content)}</code></pre>'
                text = text.replace(placeholder, html_code_block)
        
        # Шаг 13: Форматирование текста
        text = text.strip()
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
        
        # Шаг 1: Сохраняем блоки кода и inline код
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        
        # Шаг 2: Экранируем HTML-специальные символы
        text = html.escape(text)
        
        # Обработка списков и таблиц в простой текстовый формат
        text = format_simple_lists(text)
        text = format_simple_tables(text)
        
        # Шаг 3: Обрабатываем эмодзи
        text = process_emoji(text)
        
        # Шаг 4: Применяем функции форматирования
        logger.info(f"Перед обработкой форматирования Modern: {text[:100]}...")
        text = process_bold_italic_text(text)
        text = process_bold_text(text)
        logger.info(f"После обработки жирного Modern: {text[:100]}...")
        text = process_strikethrough_text(text)
        logger.info(f"После обработки зачеркнутого Modern: {text[:100]}...")
        text = process_underline_text(text)
        text = process_italic_text(text)
        text = process_links(text)
        logger.info(f"После всей обработки форматирования Modern: {text[:100]}...")
        
        # Шаг 5: Обработка специальных элементов
        text = process_headers(text)
        text = process_quotes(text)
        
        # Шаг 6: Восстанавливаем код
        for placeholder, code in inline_code.items():
            code_content = code[1:-1]  # Убираем обрамляющие символы `
            html_code = f'<code>{html.escape(code_content)}</code>'
            text = text.replace(placeholder, html_code)
            
        for placeholder, code_block in code_blocks.items():
            match = re.match(r'```(.*?)\n(.*?)```', code_block, re.DOTALL)
            if match:
                language = match.group(1).strip() or "code"
                code_content = match.group(2)
                html_code_block = f'<pre><code>{html.escape(code_content)}</code></pre>'
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