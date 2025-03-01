import html
import re
import logging
import emoji  # Зависимость для работы с эмодзи

logger = logging.getLogger(__name__)

def process_markdown_lists(text: str) -> str:
    """
    Обрабатывает списки в формате Markdown.
    :param text: Исходный текст.
    :return: Текст с обработанными списками.
    """
    lines = text.split('\n')
    processed_lines = []
    
    in_list = False
    list_type = None  # 'ul' или 'ol'
    list_items = []
    list_indent = 0
    
    for line in lines:
        # Проверяем маркированный список
        ul_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        # Проверяем нумерованный список
        ol_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        
        if ul_match:
            indent = len(ul_match.group(1))
            content = ul_match.group(2)
            
            if not in_list or list_type != 'ul' or indent != list_indent:
                if in_list:
                    # Завершаем текущий список
                    if list_type == 'ul':
                        processed_lines.append('</ul>')
                    else:
                        processed_lines.append('</ol>')
                    
                # Начинаем новый маркированный список
                processed_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
                list_indent = indent
            
            processed_lines.append(f'<li>{content}</li>')
            
        elif ol_match:
            indent = len(ol_match.group(1))
            number = ol_match.group(2)
            content = ol_match.group(3)
            
            if not in_list or list_type != 'ol' or indent != list_indent:
                if in_list:
                    # Завершаем текущий список
                    if list_type == 'ul':
                        processed_lines.append('</ul>')
                    else:
                        processed_lines.append('</ol>')
                    
                # Начинаем новый нумерованный список
                processed_lines.append(f'<ol start="{number}">')
                in_list = True
                list_type = 'ol'
                list_indent = indent
            
            processed_lines.append(f'<li>{content}</li>')
            
        else:
            if in_list:
                # Завершаем текущий список
                if list_type == 'ul':
                    processed_lines.append('</ul>')
                else:
                    processed_lines.append('</ol>')
                in_list = False
                list_type = None
            
            processed_lines.append(line)
    
    # Завершаем список, если он есть в конце текста
    if in_list:
        if list_type == 'ul':
            processed_lines.append('</ul>')
        else:
            processed_lines.append('</ol>')
    
    return '\n'.join(processed_lines)


def process_markdown_code_blocks(text: str) -> str:
    """
    Обрабатывает блоки кода в формате Markdown.
    :param text: Исходный текст.
    :return: Текст с обработанными блоками кода.
    """
    # Обработка блоков кода с указанием языка ```python ... ```
    pattern = r'```(.*?)\n(.*?)```'
    
    def replace_code_block(match):
        language = match.group(1).strip() or "code"
        code = match.group(2)
        # В Telegram нет возможности указать язык, но можно добавить его в комментарий
        return f'<pre><code class="{language}">{html.escape(code)}</code></pre>'
    
    text = re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
    
    return text


def process_markdown_tables(text: str) -> str:
    """
    Обрабатывает таблицы в формате Markdown.
    Примечание: Telegram не поддерживает таблицы как HTML-элементы,
    но мы можем попытаться их хотя бы красиво отформатировать.
    :param text: Исходный текст.
    :return: Текст с обработанными таблицами.
    """
    lines = text.split('\n')
    processed_lines = []
    
    in_table = False
    table_content = []
    
    for i, line in enumerate(lines):
        if re.match(r'^\|.*\|$', line) and not in_table:
            # Начало таблицы (первая строка с |)
            in_table = True
            table_content.append(line)
        elif in_table and re.match(r'^\|[-:| ]+\|$', line):
            # Разделитель заголовков таблицы
            table_content.append(line)
        elif in_table and re.match(r'^\|.*\|$', line):
            # Строка таблицы
            table_content.append(line)
        elif in_table:
            # Конец таблицы (строка без |)
            processed_table = format_markdown_table(table_content)
            processed_lines.append(processed_table)
            processed_lines.append(line)
            in_table = False
            table_content = []
        else:
            processed_lines.append(line)
    
    # Обработка таблицы в конце текста
    if in_table:
        processed_table = format_markdown_table(table_content)
        processed_lines.append(processed_table)
    
    return '\n'.join(processed_lines)


def format_markdown_table(table_lines: list) -> str:
    """
    Форматирует таблицу Markdown в более читаемый вид для Telegram.
    :param table_lines: Строки таблицы Markdown.
    :return: Отформатированная таблица.
    """
    if len(table_lines) < 3:
        # Неполная таблица, возвращаем как есть
        return '\n'.join(table_lines)
    
    header = table_lines[0]
    cells = [cell.strip() for cell in header.split('|')[1:-1]]
    
    # Создаем форматированную таблицу в виде текста с жирными заголовками
    formatted_header = '<b>' + ' | '.join(cells) + '</b>'
    
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        rows.append(' | '.join(cells))
    
    return f"{formatted_header}\n{'—' * 20}\n" + '\n'.join(rows)


def process_emoji(text: str) -> str:
    """
    Обрабатывает эмодзи и их текстовые коды.
    :param text: Исходный текст.
    :return: Текст с обработанными эмодзи.
    """
    # Заменяем текстовые коды эмодзи на Unicode символы
    pattern = r':([a-zA-Z0-9_\-+]+):'
    
    def replace_emoji_code(match):
        emoji_code = match.group(1)
        try:
            return emoji.emojize(f':{emoji_code}:', language='alias')
        except Exception as e:
            logger.warning(f"Не удалось преобразовать эмодзи код :{emoji_code}: - {e}")
            # Если эмодзи не найден, возвращаем исходный текст
            return f':{emoji_code}:'
    
    return re.sub(pattern, replace_emoji_code, text)


def process_headers(text: str) -> str:
    """
    Обрабатывает заголовки Markdown (# Заголовок).
    :param text: Исходный текст.
    :return: Текст с обработанными заголовками.
    """
    # Заголовок первого уровня
    text = re.sub(r'^#\s+(.*)$', r'<b><u>\1</u></b>', text, flags=re.MULTILINE)
    # Заголовок второго уровня
    text = re.sub(r'^#{2}\s+(.*)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Заголовки третьего и более уровней
    text = re.sub(r'^#{3,6}\s+(.*)$', r'<i><b>\1</b></i>', text, flags=re.MULTILINE)
    
    return text


def process_quotes(text: str) -> str:
    """
    Обрабатывает цитаты Markdown (> текст).
    :param text: Исходный текст.
    :return: Текст с обработанными цитатами.
    """
    # Обработка простых цитат
    text = re.sub(r'^>\s*(.*)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    return text


def process_horizontal_rules(text: str) -> str:
    """
    Обрабатывает горизонтальные линии (---, ***, ___).
    :param text: Исходный текст.
    :return: Текст с обработанными горизонтальными линиями.
    """
    # Заменяем на визуальный разделитель
    text = re.sub(r'^([-*_]{3,})$', r'\n<i>— — — — — — — — — —</i>\n', text, flags=re.MULTILINE)
    
    return text


def extract_and_save_placeholders(text: str, pattern: str) -> (str, dict):
    """
    Извлекает блоки, соответствующие шаблону, и заменяет их плейсхолдерами.
    :param text: Исходный текст.
    :param pattern: Регулярное выражение для поиска блоков.
    :return: Кортеж из измененного текста и словаря плейсхолдеров.
    """
    placeholders = {}
    
    def save_match(match):
        placeholder = f"__PLACEHOLDER_{len(placeholders)}__"
        placeholders[placeholder] = match.group(0)
        return placeholder
    
    modified_text = re.sub(pattern, save_match, text, flags=re.DOTALL)
    
    return modified_text, placeholders


def restore_placeholders(text: str, placeholders: dict) -> str:
    """
    Восстанавливает плейсхолдеры обратно в текст.
    :param text: Текст с плейсхолдерами.
    :param placeholders: Словарь с соответствиями плейсхолдеров и оригинального текста.
    :return: Восстановленный текст.
    """
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    
    return text