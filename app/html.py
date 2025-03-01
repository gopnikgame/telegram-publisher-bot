import logging
import html  # Для экранирования HTML
import re

from .markdown import (
    process_markdown_lists, process_markdown_code_blocks, process_markdown_tables, 
    process_emoji, process_headers, process_quotes, process_horizontal_rules,
    extract_and_save_placeholders, restore_placeholders,
    process_bold_text, process_italic_text, process_strikethrough_text,
    process_underline_text, process_bold_italic_text, process_links, process_code
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
        
        # Применяем функции форматирования из модуля markdown
        text = process_emoji(text)  # Обработка эмодзи
        text = process_bold_italic_text(text)  # ***жирный курсив*** -> <strong><em>жирный курсив</em></strong>
        logger.info(f"После обработки супержирного: {text[:100]}...")
        text = process_bold_text(text)  # **жирный** -> <strong>жирный</strong>
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = process_strikethrough_text(text)  # ~~зачеркнутый~~ -> <del>зачеркнутый</del>
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = process_underline_text(text)  # __подчеркнутый__ -> <u>подчеркнутый</u>
        text = process_italic_text(text)  # _курсив_, *курсив* -> <em>курсив</em>
        text = process_code(text)  # `код` -> <code>код</code>
        text = process_links(text)  # [текст](ссылка) -> <a href="ссылка">текст</a>
        
        # Дополнительная обработка элементов из модуля markdown
        text = process_markdown_lists(text)
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
        
        # Шаг 1-2: Сохраняем блоки кода и inline код
        text, code_blocks = extract_and_save_placeholders(text, r'```.*?\n.*?```')
        text, inline_code = extract_and_save_placeholders(text, r'`[^`]+`')
        
        # Шаг 3: Экранируем HTML-специальные символы
        text = html.escape(text)
        logger.info(f"После экранирования HTML: {text[:100]}...")
        
        # Шаг 4-9: Обработка различных элементов Markdown
        text = process_emoji(text)
        text = process_markdown_tables(text)
        text = process_markdown_lists(text)
        text = process_headers(text)
        text = process_quotes(text)
        text = process_horizontal_rules(text)
        
        # Шаг 10: Применяем функции форматирования
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
                html_code_block = f'<pre><code class="{language}">{html.escape(code_content)}</code></pre>'
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
        text = process_markdown_lists(text)
        text = process_quotes(text)
        text = process_headers(text)
        
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