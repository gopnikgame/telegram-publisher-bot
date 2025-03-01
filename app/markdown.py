import logging
import re
import random
import string
import html
from typing import Dict, Tuple, List


def extract_and_save_placeholders(text: str, pattern: str) -> Tuple[str, Dict[str, str]]:
    """
    Извлекает из текста части, соответствующие шаблону, и заменяет их плейсхолдерами.
    
    Args:
        text: Исходный текст
        pattern: Регулярное выражение для поиска
        
    Returns:
        Tuple[str, Dict[str, str]]: Текст с плейсхолдерами и словарь соответствий плейсхолдер -> исходный текст
    """
    matches = re.findall(pattern, text, re.DOTALL)
    placeholders = {}
    
    for match in matches:
        # Генерируем уникальный плейсхолдер
        placeholder = f"PLACEHOLDER_{random.randint(10000, 99999)}_{''.join(random.choices(string.ascii_letters, k=5))}"
        
        # Заменяем полное совпадение, а не только группу
        original_text = match if isinstance(match, str) else match[0]
        text = text.replace(original_text, placeholder, 1)
        placeholders[placeholder] = original_text
    
    return text, placeholders

def restore_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    """
    Восстанавливает оригинальный текст из плейсхолдеров.
    
    Args:
        text: Текст с плейсхолдерами
        placeholders: Словарь соответствий плейсхолдер -> исходный текст
        
    Returns:
        str: Текст с восстановленными оригинальными частями
    """
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    
    return text

def process_emoji(text: str) -> str:
    """Замена стандартных эмодзи на HTML-эмодзи."""
    # Данная функция оставляет эмодзи без изменений, так как Telegram их поддерживает
    return text

def process_bold_text(text: str) -> str:
    """Обрабатывает жирный текст в формате Markdown и преобразует его в HTML."""
    # Обработка жирного текста (** вариант)
    pattern = r'\*\*(.*?)\*\*'
    text = re.sub(pattern, r'<b>\1</b>', text)
    
    return text

def process_italic_text(text: str) -> str:
    """Обрабатывает курсивный текст в формате Markdown и преобразует его в HTML."""
    # Обработка курсивного текста (* вариант)
    pattern = r'\*(.*?)\*'
    text = re.sub(pattern, r'<i>\1</i>', text)
    
    return text

def process_bold_italic_text(text: str) -> str:
    """Обрабатывает жирный курсивный текст в формате Markdown и преобразует его в HTML."""
    # Обработка жирного курсивного текста (*** вариант)
    pattern = r'\*\*\*(.*?)\*\*\*'
    text = re.sub(pattern, r'<b><i>\1</i></b>', text)
    
    return text

def process_strikethrough_text(text: str) -> str:
    """Обрабатывает зачеркнутый текст в формате Markdown и преобразует его в HTML."""
    # Обработка зачеркнутого текста (~~ вариант)
    pattern = r'~~(.*?)~~'
    text = re.sub(pattern, r'<s>\1</s>', text)
    
    return text

def process_underline_text(text: str) -> str:
    """Обрабатывает подчеркнутый текст в формате Markdown и преобразует его в HTML."""
    # Обработка подчеркнутого текста (__$ вариант$__)
    pattern = r'__\$(.*?)\$__'
    text = re.sub(pattern, r'<u>\1</u>', text)
    
    return text

def process_code(text: str) -> str:
    """Обрабатывает код в формате Markdown и преобразует его в HTML."""
    # Обработка инлайн-кода (` вариант)
    pattern = r'`([^`]+)`'
    text = re.sub(pattern, r'<code>\1</code>', text)
    
    # Обработка блока кода (``` вариант)
    pattern = r'```(.*?)\n(.*?)```'
    text = re.sub(pattern, r'<pre>\2</pre>', text, flags=re.DOTALL)
    
    return text

def process_quotes(text: str) -> str:
    """Обрабатывает цитаты в формате Markdown и преобразует их в HTML."""
    # Обработка цитат (начинаются с > )
    lines = text.split('\n')
    result = []
    in_quote = False
    quote_lines = []
    
    for line in lines:
        if line.startswith('> '):
            # Начало или продолжение цитаты
            if not in_quote:
                in_quote = True
            quote_lines.append(line[2:])  # Убираем "> " из начала строки
        else:
            # Конец цитаты, если была активна
            if in_quote:
                result.append(f'<blockquote>{" ".join(quote_lines)}</blockquote>')
                quote_lines = []
                in_quote = False
            result.append(line)
    
    # Если цитата не была закрыта
    if in_quote:
        result.append(f'<blockquote>{" ".join(quote_lines)}</blockquote>')
    
    return '\n'.join(result)

def process_headers(text: str) -> str:
    """Обрабатывает заголовки в формате Markdown и преобразует их в HTML."""
    # Обработка заголовков (# вариант)
    lines = text.split('\n')
    result = []
    
    for line in lines:
        # Обработка заголовков h1-h6
        header_match = re.match(r'^(#{1,6})\s+(.*?)$', line)
        if header_match:
            level = len(header_match.group(1))
            content = header_match.group(2)
            result.append(f'<h{level}>{content}</h{level}>')
        else:
            result.append(line)
    
    return '\n'.join(result)

def process_links(text: str) -> str:
    """Обрабатывает ссылки в формате Markdown и преобразует их в HTML."""
    # Обработка ссылок [текст](url)
    pattern = r'\[(.*?)\]\((.*?)\)'
    text = re.sub(pattern, r'<a href="\2">\1</a>', text)
    
    return text

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

def process_simple_horizontal_rules(text: str) -> str:
    """Заменяет горизонтальные линии на простые текстовые разделители."""
    text = re.sub(r'^---+$', '----------', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*\*+$', '----------', text, flags=re.MULTILINE)
    text = re.sub(r'^___+$', '----------', text, flags=re.MULTILINE)
    return text

def format_table_as_text(table_data):
    """
    Форматирует данные таблицы в виде простого текста без тегов HTML.
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
        
        # Добавляем разделитель после заголовка в виде текстовой строки (не HTML)
        if i == 0:
            separator = "-" * len(formatted_row)
            formatted_rows.append(separator)
    
    return '\n'.join(formatted_rows)

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