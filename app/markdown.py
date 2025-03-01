import re
import logging
import html

logger = logging.getLogger(__name__)

def extract_and_save_placeholders(text, pattern):
    """
    Извлекает части текста по шаблону и заменяет их временными плейсхолдерами.
    Возвращает измененный текст и словарь плейсхолдеров.
    """
    if not text:
        return text, {}
        
    placeholders = {}
    matches = re.findall(pattern, text, re.DOTALL)
    
    for i, match in enumerate(matches):
        placeholder = f"__PLACEHOLDER_{i}__"
        content = match if isinstance(match, str) else match[0]  # Получаем содержимое match
        start_idx = text.find(content)
        if start_idx != -1:
            text = text[:start_idx] + placeholder + text[start_idx + len(content):]
            placeholders[placeholder] = content
            
    return text, placeholders

def restore_placeholders(text, placeholders):
    """Восстанавливает плейсхолдеры в тексте из словаря."""
    for placeholder, content in placeholders.items():
        text = text.replace(placeholder, content)
    return text

def process_emoji(text):
    """
    Обработка эмодзи. Пока просто возвращаем текст как есть, 
    так как эмодзи обрабатываются Telegram автоматически.
    """
    return text


def convert_table_to_html(table_lines):
    """
    Преобразует строки таблицы Markdown в HTML таблицу.
    """
    html_lines = ['<table>']
    
    for i, line in enumerate(table_lines):
        if i == 1 and re.match(r'^\s*\|([-:]+\|)+\s*$', line):  # Разделитель заголовка и тела
            continue
            
        # Удаляем начальный и конечный разделитель и разбиваем на ячейки
        cells = [cell.strip() for cell in line.strip('| \t').split('|')]
        
        if i == 0:  # Заголовок таблицы
            html_lines.append('<thead><tr>')
            for cell in cells:
                html_lines.append(f'<th>{cell}</th>')
            html_lines.append('</tr></thead><tbody>')
        else:
            html_lines.append('<tr>')
            for cell in cells:
                html_lines.append(f'<td>{cell}</td>')
            html_lines.append('</tr>')
            
    html_lines.append('</tbody></table>')
    return '\n'.join(html_lines)

def process_headers(text):
    """
    Обработка заголовков Markdown.
    # Заголовок 1
    ## Заголовок 2
    ### Заголовок 3
    """
    # Заголовок 1 уровня
    text = re.sub(r'^# (.+)$', r'<b><u>\1</u></b>', text, flags=re.MULTILINE)
    # Заголовок 2 уровня
    text = re.sub(r'^## (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Заголовок 3 уровня
    text = re.sub(r'^### (.+)$', r'<i><b>\1</b></i>', text, flags=re.MULTILINE)
    # Заголовок 4 уровня
    text = re.sub(r'^#### (.+)$', r'<i>\1</i>', text, flags=re.MULTILINE)
    # Заголовок 5 уровня
    text = re.sub(r'^##### (.+)$', r'<u>\1</u>', text, flags=re.MULTILINE)
    # Заголовок 6 уровня
    text = re.sub(r'^###### (.+)$', r'<i><u>\1</u></i>', text, flags=re.MULTILINE)
    
    return text

def process_quotes(text):
    """
    Обработка цитат Markdown.
    > Цитата
    """
    lines = text.split('\n')
    result_lines = []
    in_quote = False
    quote_lines = []
    
    for line in lines:
        if line.startswith('>'):
            if not in_quote:
                in_quote = True
            quote_content = line[1:].strip()  # Убираем символ > и лишние пробелы
            quote_lines.append(quote_content)
        else:
            if in_quote:
                result_lines.append(f"<blockquote>{' '.join(quote_lines)}</blockquote>")
                quote_lines = []
                in_quote = False
            result_lines.append(line)
            
    if in_quote:  # Закрываем цитату в конце текста
        result_lines.append(f"<blockquote>{' '.join(quote_lines)}</blockquote>")
        
    return '\n'.join(result_lines)


def process_bold_text(text):
    """
    Обработка жирного текста с различными вариантами синтаксиса.
    Поддерживает форматы: **жирный**, __жирный__
    """
    # Стандартный синтаксис **жирный**
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Альтернативный синтаксис __жирный__ (если не обработан как подчеркнутый)
    text = re.sub(r'__([^_]+?)__', r'<strong>\1</strong>', text)
    return text

def process_italic_text(text):
    """
    Обработка курсивного текста с различными вариантами синтаксиса.
    Поддерживает форматы: *курсив*, _курсив_
    """
    # Синтаксис *курсив* (одна звездочка)
    text = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'<em>\1</em>', text)
    # Синтаксис _курсив_ (одно подчеркивание)
    text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<em>\1</em>', text)
    return text

def process_strikethrough_text(text):
    """
    Обработка зачеркнутого текста с различными вариантами синтаксиса.
    Поддерживает форматы: ~~зачеркнутый~~, ~зачеркнутый~
    """
    # Стандартный синтаксис ~~зачеркнутый~~
    text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)
    # Альтернативный синтаксис ~зачеркнутый~ (один символ тильды)
    text = re.sub(r'(?<!~)~([^~]+?)~(?!~)', r'<del>\1</del>', text)
    return text

def process_underline_text(text):
    """
    Обработка подчеркнутого текста.
    Поддерживает формат: __подчеркнутый__
    """
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
    return text

def process_bold_italic_text(text):
    """
    Обработка жирного курсива.
    Поддерживает формат: ***жирный курсив***
    """
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    return text

def process_links(text):
    """
    Обработка ссылок.
    Поддерживает формат: [текст](ссылка)
    """
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    return text

def process_code(text):
    """
    Обработка инлайн кода.
    Поддерживает формат: `код`
    """
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    return text