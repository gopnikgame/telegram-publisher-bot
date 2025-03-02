import logging
import os
import re
import textwrap
from datetime import datetime
from typing import Dict, Optional, List, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler, Application

from .html import recreate_markdown_from_entities, markdown_to_html, modern_to_html
from .config import config
# Импортируем все необходимые функции из utils.py
from .utils import format_message, format_bot_links, append_links_to_message

# Настройка логирования
logger = logging.getLogger(__name__)

# [Остальной код остается без изменений...]

# Заменяем функцию create_footer() на прямой вызов format_bot_links из utils.py
def create_footer() -> str:
    """Создает подпись для сообщений, используя функцию из utils.py."""
    return format_bot_links('html')

# Изменяем send_formatted_message, чтобы использовать format_message из utils.py
async def send_formatted_message(
    context: CallbackContext,
    chat_id: int,
    message_text: str,
    format_type: str,
    footer: str,
    test_mode_enabled: bool = False,
    target_chat_id: Optional[int] = None
) -> None:
    """
    Отправляет форматированное сообщение.
    """
    try:
        # Используем format_message из utils.py для форматирования
        formatted_text = format_message(message_text, format_type)
        
        parse_mode = ParseMode.HTML
        
        # Остальная логика отправки сообщения...
        if test_mode_enabled:
            safe_preview = message_text.replace("<", "&lt;").replace(">", "&gt;")
            preview_message = f"📝 Предпросмотр сообщения:\n\n{safe_preview[:500]}"
            if len(safe_preview) > 500:
                preview_message += "..."
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=preview_message,
                parse_mode=None
            )
        
        if target_chat_id is None:
            target_chat_id = chat_id
        
        message = await context.bot.send_message(
            chat_id=target_chat_id,
            text=formatted_text,
            parse_mode=parse_mode,
            disable_web_page_preview=False
        )
        
        success_message = "✅ Сообщение успешно отправлено."
        if test_mode_enabled:
            success_message += f"\nID сообщения: {message.message_id}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=success_message
        )
        logger.info(f"Сообщение успешно отправлено в чат {target_chat_id}. ID сообщения: {message.message_id}")
    except Exception as e:
        error_message = str(e)
        logger.error(f"Ошибка при отправке сообщения в чат {target_chat_id}: {error_message}", exc_info=True)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка при отправке сообщения: {error_message}"
        )
        
        if test_mode_enabled:
            safe_text = message_text.replace("<", "&lt;").replace(">", "&gt;")
            debug_info = (
                f"🔍 Детали ошибки:\n\n"
                f"Целевой чат: {target_chat_id}\n"
                f"Формат: {format_type}\n"
                f"Режим парсинга: {parse_mode}\n"
                f"Текст с ошибкой (часть): {safe_text[:300]}..."
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=debug_info
            )

# В функции start используем append_links_to_message из utils.py
async def start(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /start."""
    chat_id = update.effective_chat.id
    
    # Создаем приветственное сообщение
    message = (
        "👋 Привет! Я бот для форматирования текста.\n\n"
        "Отправьте мне текст, и я помогу вам отформатировать его для Telegram.\n"
        "Чтобы выбрать формат, используйте команду /format.\n\n"
        "Команды:\n"
        "/start - Показать это сообщение\n"
        "/help - Показать справку по форматированию\n"
        "/format - Выбрать формат сообщения"
    )
    
    # Добавляем команды администратора для админов
    user_id = update.effective_user.id
    if check_admin(user_id):
        message += "\n\nКоманды администратора:\n"
        message += "/test - Включить/выключить тестовый режим\n"
        message += "/setformat [тип] - Установить формат по умолчанию (markdown, html, modern)"
    
    # Используем append_links_to_message из utils.py для добавления подписи
    message = append_links_to_message(message, 'html')
    
    # Отправляем сообщение
    try:
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при отправке стартового сообщения: {str(e)}", exc_info=True)
        # Попробуем отправить без форматирования
        await context.bot.send_message(
            chat_id=chat_id, 
            text="👋 Привет! Я бот для форматирования текста. Используйте /format для выбора формата."
        )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /help."""
    chat_id = update.effective_chat.id
    
    message = (
        "📚 *Справка по форматированию*\n\n"
        "*Поддерживаемые форматы:*\n"
        "• *Markdown* - базовое форматирование текста\n"
        "• *HTML* - продвинутое форматирование с HTML-тегами\n\n"
        "*Примеры Markdown:*\n"
        "• **Жирный текст** для жирного\n"
        "• *Курсив* для курсива\n"
        "• ~~Зачеркнутый~~ для зачеркнутого\n"
        "• `Код` для монопространственного шрифта\n"
        "• ```\nБлок кода\n``` для блока кода\n"
        "• > Цитата для цитирования\n"
        "• # Заголовок для заголовков\n"
        "• 1. Пункт для нумерованных списков\n"
        "• - Пункт для маркированных списков\n"
        "• [Текст](https://example.com) для ссылок\n\n"
        "Используйте команду /format, чтобы выбрать предпочтительный формат."
    )
    
    # Создаем подпись
    footer = create_footer()
    if footer:
        message += footer
    
    # Отправляем сообщение с Markdown форматированием вместо HTML
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=message, 
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке справочного сообщения: {str(e)}", exc_info=True)
        # Попробуем отправить без форматирования
        await context.bot.send_message(
            chat_id=chat_id, 
            text="Справка по форматированию доступна в /format. Выберите формат для вашего текста."
        )

async def format_command(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /format."""
    chat_id = update.effective_chat.id
    
    # Создаем клавиатуру для выбора формата
    keyboard = [
        [
            InlineKeyboardButton("Markdown", callback_data="format_markdown"),
            InlineKeyboardButton("HTML", callback_data="format_html"),
        ],
        [
            InlineKeyboardButton("Modern", callback_data="format_modern"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
     
    # Отправляем сообщение с клавиатурой
    await context.bot.send_message(
        chat_id=chat_id,
        text="Выберите формат для отправки сообщений:",
        reply_markup=reply_markup
    )
    
    # Устанавливаем состояние пользователя
    user_id = update.effective_user.id
    user_states[user_id] = STATE_AWAITING_FORMAT

async def test_mode(update: Update, context: CallbackContext) -> None:
    """Включает/выключает тестовый режим."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверка на право использования команды
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Только администраторы могут использовать эту команду."
        )
        return
    
    # Переключаем режим
    current_state = user_states.get(user_id, STATE_NORMAL)
    new_state = STATE_TEST_MODE if current_state != STATE_TEST_MODE else STATE_NORMAL
    user_states[user_id] = new_state
    
    # Отправляем сообщение о текущем статусе
    status_message = "✅ Тестовый режим включен" if new_state == STATE_TEST_MODE else "❌ Тестовый режим выключен"
    await context.bot.send_message(chat_id=chat_id, text=status_message)
    
    logger.info(f"Администратор {user_id} {'включил' if new_state == STATE_TEST_MODE else 'выключил'} тестовый режим")

async def set_format(update: Update, context: CallbackContext) -> None:
    """Устанавливает формат по умолчанию."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверка на право использования команды
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Только администраторы могут использовать эту команду."
        )
        return
    
    # Проверяем, что формат указан
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Укажите формат: /setformat [markdown|html|modern]"
        )
        return
    
    # Получаем формат из аргументов
    format_type = context.args[0].lower()
    
    # Проверяем, что формат корректный
    valid_formats = ["markdown", "html", "modern"]
    if format_type not in valid_formats:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Неверный формат. Используйте один из следующих: {', '.join(valid_formats)}"
        )
        return
    
    # Устанавливаем формат по умолчанию
    context.bot_data["default_format"] = format_type
    
    # Отправляем сообщение о текущем статусе
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Формат по умолчанию установлен: {format_type}"
    )
    
    logger.info(f"Администратор {user_id} установил формат по умолчанию: {format_type}")

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает нажатия на кнопки."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Обязательно отвечаем на запрос
    await query.answer()
    
    # Получаем данные из callback_data
    callback_data = query.data
    
    # Обрабатываем выбор формата
    if callback_data.startswith("format_"):
        format_type = callback_data.replace("format_", "")
        
        # Сохраняем выбранный формат
        context.user_data["format"] = format_type
        
        # Обновляем текст сообщения
        await query.edit_message_text(
            text=f"✅ Формат установлен: {format_type}\n\nТеперь отправьте сообщение для форматирования."
        )
        
        # Обновляем состояние пользователя
        user_states[user_id] = STATE_AWAITING_MESSAGE
        
        logger.info(f"Пользователь {user_id} выбрал формат: {format_type}")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обрабатывает обычные текстовые сообщения."""
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat_id
    
    # Получаем текст и формат сообщения
    text = message.text
    
    # Проверяем, находится ли пользователь в состоянии ожидания сообщения
    state = user_states.get(user_id, STATE_NORMAL)
    
    # Если пользователь не в состоянии ожидания формата или сообщения, устанавливаем формат по умолчанию
    if state not in (STATE_AWAITING_FORMAT, STATE_AWAITING_MESSAGE):
        format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    else:
        format_type = context.user_data.get("format", "markdown").lower()
    
    logger.info(f"Получено сообщение: {text}")
    logger.info(f"Формат сообщения: {format_type}")
    
    # Создаем подпись
    footer = create_footer()
    
    # Проверяем, находится ли пользователь в тестовом режиме
    test_mode_enabled = state == STATE_TEST_MODE
    
    # Определяем целевой чат
    if test_mode_enabled:
        target_chat_id = config.TEST_CHAT_ID if config.TEST_CHAT_ID != 0 else chat_id
    else:
        target_chat_id = config.CHANNEL_ID if config.CHANNEL_ID != 0 else chat_id
    
    await send_formatted_message(
        context,
        chat_id,
        text,
        format_type,
        footer,
        test_mode_enabled,
        target_chat_id
    )

async def send_to_channel(update: Update, context: CallbackContext) -> None:
    """
    Отправляет форматированное сообщение в канал.
    В зависимости от режима работы бота, сообщение отправляется:
    - В тестовом режиме: в TEST_CHAT_ID или себе, если TEST_CHAT_ID не указан
    - В обычном режиме: в CHANNEL_ID
    
    Использование: /send текст сообщения
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверяем права администратора
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для отправки сообщений в канал."
        )
        return
    
    # Проверяем аргументы команды
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Укажите текст сообщения: /send текст сообщения"
        )
        return
    
    # Собираем текст сообщения из всех аргументов
    message_text = ' '.join(context.args)
    
    # Определяем, включен ли тестовый режим
    test_mode_enabled = user_states.get(user_id) == STATE_TEST_MODE
    
    # Определяем целевой чат
    if test_mode_enabled:
        target_chat_id = config.TEST_CHAT_ID if config.TEST_CHAT_ID != 0 else chat_id
        target_name = "тестовый канал" if config.TEST_CHAT_ID != 0 else "текущий чат (тестовый режим)"
    else:
        target_chat_id = config.CHANNEL_ID if config.CHANNEL_ID != 0 else 0
        target_name = "основной канал" if config.CHANNEL_ID != 0 else ""
    
    if target_chat_id == 0:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ ID канала не установлен в конфигурации."
        )
        return
    
    # Определяем формат сообщения (используем сохраненный пользователем или формат по умолчанию)
    format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    logger.info(f"Формат сообщения для канала: {format_type}")
    
    await send_formatted_message(
        context,
        chat_id,
        message_text,
        format_type,
        create_footer(),
        test_mode_enabled,
        target_chat_id
    )

async def check_channels(update: Update, context: CallbackContext) -> None:
    """
    Проверяет права бота в настроенных каналах и выводит информацию о них.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверяем права администратора
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для выполнения этой команды."
        )
        return
    
    # Собираем список каналов из конфигурации
    channels = []
    
    if hasattr(config, 'CHANNEL_ID') and config.CHANNEL_ID != 0:
        channels.append(("Основной канал", config.CHANNEL_ID))
    
    if hasattr(config, 'TEST_CHAT_ID') and config.TEST_CHAT_ID != 0:
        channels.append(("Тестовый канал", config.TEST_CHAT_ID))
    
    if not channels:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ В конфигурации не найдены ID каналов."
        )
        return
    
    # Проверяем доступ к каналам
    result = "📊 Информация о каналах:\n\n"
    
    for name, channel_id in channels:
        try:
            # Пробуем получить информацию о чате
            chat_info = await context.bot.get_chat(channel_id)
            
            # Проверяем права бота в канале
            bot_member = await context.bot.get_chat_member(
                chat_id=channel_id,
                user_id=context.bot.id
            )
            
            # Формируем строку статуса
            status = "✅ Доступен"
            if hasattr(bot_member, 'can_post_messages') and not bot_member.can_post_messages:
                status = "⚠️ Нет прав на отправку сообщений"
            
            # Добавляем информацию о канале
            result += f"{name} ({channel_id}):\n"
            result += f"Название: {chat_info.title}\n"
            result += f"Тип: {chat_info.type}\n"
            result += f"Статус: {status}\n\n"
            
        except Exception as e:
            result += f"{name} ({channel_id}):\n"
            result += f"Статус: ❌ Ошибка доступа ({str(e)})\n\n"
    
    # Отправляем результат проверки
    await context.bot.send_message(
        chat_id=chat_id,
        text=result
    )

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ошибки."""
    error = context.error
    logger.error(msg=f"Произошла ошибка: {error}", exc_info=True)
    
    try:
        if update and update.effective_chat:
            chat_id = update.effective_chat.id
            
            # Формируем сообщение об ошибке
            error_message = "Извините, произошла ошибка при обработке вашего запроса."
            
            # Проверяем тип ошибки
            if isinstance(error, BadRequest):
                error_message = f"Ошибка запроса: {str(error)}"
            
            # Для админов показываем более подробную информацию
            user_id = update.effective_user.id if update.effective_user else None
            if user_id and check_admin(user_id):
                error_message += f"\n\nДетали ошибки: {str(error)}"
                
                # Добавляем информацию о контексте
                if hasattr(context, 'chat_data') and context.chat_data:
                    error_message += f"\n\nДанные чата: {str(context.chat_data)}"
                if hasattr(context, 'user_data') and context.user_data:
                    error_message += f"\n\nДанные пользователя: {str(context.user_data)}"
             
            await context.bot.send_message(
                chat_id=chat_id,
                text=error_message
            )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}", exc_info=True)

def setup_handlers(application: Application) -> None:
    """
    Устанавливает обработчики сообщений и команд для бота.
    
    Args:
        application: Экземпляр Application для установки обработчиков
    """
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("format", format_command))
    
    # Регистрируем обработчики команд для администраторов
    application.add_handler(CommandHandler("test", test_mode))
    application.add_handler(CommandHandler("setformat", set_format))
    application.add_handler(CommandHandler("send", send_to_channel))  # Команда для отправки в канал
    application.add_handler(CommandHandler("channels", check_channels))  # Команда для проверки каналов
    
    # Регистрируем обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Регистрируем обработчик для обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    logger.info("Обработчики сообщений установлены")