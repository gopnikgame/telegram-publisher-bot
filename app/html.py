import logging
import html  # Для экранирования HTML
import re

from .markdown import (
    process_emoji, process_headers, process_quotes, 
    extract_and_save_placeholders, restore_placeholders,
    process_bold_text, process_italic_text, process_strikethrough_text,
    process_underline_text, process_bold_italic_text, process_links, process_code,
    process_simple_horizontal_rules, format_simple_tables, format_simple_lists,
    process_images  # Добавлен импорт новой функции
)

logger = logging.getLogger(__name__)  # Получаем логгер

def is_html_formatted(text: str) -> bool:
    """Проверяет, содержит ли текст HTML-теги, поддерживаемые Telegram API."""
    # Обновленный список тегов в соответствии с документацией Telegram API
    html_tags_pattern = re.compile(r'<(/?)(b|strong|i|em|u|s|strike|del|code|pre|a)(\s+[^>]*)?>')
    return bool(html_tags_pattern.search(text))

# Функция для восстановления маркеров Markdown из объекта entities
def recreate_markdown_from_entities(text: str, entities: list) -> str:
    """
    Восстанавливает маркеры Markdown из объекта entities.
    """
    if not entities:
        return text
        
    # Сортируем сущности в обратном порядке, чтобы начать с конца текста
    # Это позволяет не менять индексы при вставке
    sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    
    # Создаем копию текста для модификации
    result = text
    
    for entity in sorted_entities:
        start = entity.offset
        end = entity.offset + entity.length
        
        # Получаем текст внутри сущности
        entity_text = text[start:end]
        
        # В зависимости от типа сущности добавляем соответствующие маркеры
        if entity.type == "bold":
            formatted_text = f"**{entity_text}**"
        elif entity.type == "italic":
            formatted_text = f"*{entity_text}*"
        elif entity.type == "code":
            formatted_text = f"`{entity_text}`"
        elif entity.type == "pre":
            formatted_text = f"```\n{entity_text}\n```"
        elif entity.type == "text_link":
            formatted_text = f"[{entity_text}]({entity.url})"
        elif entity.type == "strikethrough":
            formatted_text = f"~~{entity_text}~~"
        elif entity.type == "underline":
            formatted_text = f"__${entity_text}$__"
        # Добавляем другие типы при необходимости
        else:
            continue  # Если не можем обработать, пропускаем
        
        # Заменяем часть текста на текст с маркерами
        result = result[:start] + formatted_text + result[end:]
    
    return result

def format_html(text: str) -> str:
    """Форматирует текст в HTML, поддерживаемый Telegram API."""
    if is_html_formatted(text):
        logger.info("Обнаружена HTML-разметка, пропускаем экранирование")
    else:
        logger.info("Конвертируем разметку в HTML")
        text = html.escape(text)
        logger.info(f"Текст после экранирования HTML: {text[:100]}...")
        
        # Сначала преобразуем списки и таблицы в простой текст
        text = format_simple_lists(text)
        text = format_simple_tables(text)
        text = process_simple_horizontal_rules(text)
        
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
        text = process_simple_horizontal_rules(text)
        
        # Шаг 4-9: Базовая обработка Markdown
        text = process_emoji(text)
        text = process_images(text)  # Обработка изображений должна идти до обработки ссылок
        text = process_headers(text)  # Используем обновленную функцию
        text = process_quotes(text)   # Используем обновленную функцию
        
        # Шаг 10: Базовое форматирование текста
        logger.info(f"Текст перед обработкой форматирования: {text[:100]}...")
        text = process_bold_italic_text(text)
        text = process_bold_text(text)  # Используем обновленную функцию
        logger.info(f"После обработки жирного: {text[:100]}...")
        text = process_strikethrough_text(text)  # Используем обновленную функцию
        logger.info(f"После обработки зачеркнутого: {text[:100]}...")
        text = process_underline_text(text)
        text = process_italic_text(text)
        text = process_links(text)  # Используем обновленную функцию
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
                # Используем <pre> без вложенного <code> для лучшей совместимости
                html_code_block = f'<pre>{html.escape(code_content)}</pre>'
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
        text = process_simple_horizontal_rules(text)
        
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
                # Используем <pre> без вложенного <code> для лучшей совместимости
                html_code_block = f'<pre>{html.escape(code_content)}</pre>'
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