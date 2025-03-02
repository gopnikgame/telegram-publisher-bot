import logging
from datetime import datetime
from typing import Dict, Optional, List, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, Application

from .html import recreate_markdown_from_entities, markdown_to_html, modern_to_html
from .config import config
from .utils import format_message, check_file_size, setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Словарь для хранения состояний пользователя
user_states = {}

# Константы для состояний пользователя
STATE_AWAITING_FORMAT = 'awaiting_format'
STATE_AWAITING_MESSAGE = 'awaiting_message'
STATE_NORMAL = 'normal'
STATE_TEST_MODE = 'test_mode'

# Список администраторов (ID пользователей)
ADMIN_IDS = [
    int(admin_id.strip()) for admin_id in config.ADMIN_IDS.split(',')
] if isinstance(config.ADMIN_IDS, str) else [
    int(admin_id) if isinstance(admin_id, str) else admin_id for admin_id in config.ADMIN_IDS
] if isinstance(config.ADMIN_IDS, list) else []

logger.info(f"Загружены ID администраторов: {ADMIN_IDS}")


def check_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        bool: True, если пользователь администратор, иначе False
    """
    return user_id in ADMIN_IDS


async def start(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /start."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    message = (
        "👋 Привет! Я бот для форматирования текста.\n\n"
        "Отправьте мне текст, и я помогу вам отформатировать его для Telegram.\n"
        "Чтобы выбрать формат, используйте команду /format.\n\n"
        "Команды:\n"
        "/start - Показать это сообщение\n"
        "/help - Показать справку по форматированию\n"
        "/format - Выбрать формат сообщения"
    )
    
    if check_admin(user_id):
        message += "\n\nКоманды администратора:\n"
        message += "/test - Включить/выключить тестовый режим\n"
        message += "/setformat [тип] - Установить формат по умолчанию (markdown, html, modern)"
    
    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error(f"Ошибка при отправке стартового сообщения: {str(e)}", exc_info=True)
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
    
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=message, 
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке справочного сообщения: {str(e)}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id, 
            text="Справка по форматированию доступна в /format. Выберите формат для вашего текста."
        )


async def format_command(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /format."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
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
    
    await context.bot.send_message(
        chat_id=chat_id,
        text="Выберите формат для отправки сообщений:",
        reply_markup=reply_markup
    )
    
    user_states[user_id] = STATE_AWAITING_FORMAT


async def test_mode(update: Update, context: CallbackContext) -> None:
    """Включает/выключает тестовый режим."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Только администраторы могут использовать эту команду."
        )
        return
    
    current_state = user_states.get(user_id, STATE_NORMAL)
    new_state = STATE_TEST_MODE if current_state != STATE_TEST_MODE else STATE_NORMAL
    user_states[user_id] = new_state
    
    status_message = "✅ Тестовый режим включен" if new_state == STATE_TEST_MODE else "❌ Тестовый режим выключен"
    await context.bot.send_message(chat_id=chat_id, text=status_message)
    
    logger.info(f"Администратор {user_id} {'включил' if new_state == STATE_TEST_MODE else 'выключил'} тестовый режим")


async def set_format(update: Update, context: CallbackContext) -> None:
    """Устанавливает формат по умолчанию."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Только администраторы могут использовать эту команду."
        )
        return
    
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Укажите формат: /setformat [markdown|html|modern]"
        )
        return
    
    format_type = context.args[0].lower()
    valid_formats = ["markdown", "html", "modern"]
    
    if format_type not in valid_formats:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Неверный формат. Используйте один из следующих: {', '.join(valid_formats)}"
        )
        return
    
    context.bot_data["default_format"] = format_type
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Формат по умолчанию установлен: {format_type}"
    )
    
    logger.info(f"Администратор {user_id} установил формат по умолчанию: {format_type}")


async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает нажатия на кнопки."""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("format_"):
        format_type = callback_data.replace("format_", "")
        context.user_data["format"] = format_type
        
        await query.edit_message_text(
            text=f"✅ Формат установлен: {format_type}\n\nТеперь отправьте сообщение для форматирования."
        )
        
        user_states[user_id] = STATE_AWAITING_MESSAGE
        
        logger.info(f"Пользователь {user_id} выбрал формат: {format_type}")


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
    
    Args:
        context: Контекст обратного вызова.
        chat_id: ID чата, куда отправляется сообщение.
        message_text: Текст сообщения.
        format_type: Тип формата (markdown, html, modern).
        footer: Подпись для сообщения.
        test_mode_enabled: Флаг тестового режима.
        target_chat_id: ID целевого чата для отправки сообщения.
    """
    try:
        formatted_text = format_message(message_text, format_type)
        
        if footer:
            formatted_text += footer
        
        parse_mode = ParseMode.HTML
        
        if test_mode_enabled:
            safe_preview = message_text.replace(" ", " >")
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
            safe_text = message_text.replace(" ", " >")
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


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обрабатывает обычные текстовые сообщения."""
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat_id
    text = message.text
    
    state = user_states.get(user_id, STATE_NORMAL)
    
    if state not in (STATE_AWAITING_FORMAT, STATE_AWAITING_MESSAGE):
        format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    else:
        format_type = context.user_data.get("format", "markdown").lower()
    
    logger.info(f"Получено сообщение: {text}")
    logger.info(f"Формат сообщения: {format_type}")
    
    footer = ""
    
    test_mode_enabled = state == STATE_TEST_MODE
    
    await send_formatted_message(
        context,
        chat_id,
        text,
        format_type,
        footer,
        test_mode_enabled,
        config.CHANNEL_ID if not test_mode_enabled and chat_id != user_id else None
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
    
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для отправки сообщений в канал."
        )
        return
    
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Укажите текст сообщения: /send текст сообщения"
        )
        return
    
    message_text = ' '.join(context.args)
    test_mode_enabled = user_states.get(user_id) == STATE_TEST_MODE
    
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
    
    format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    logger.info(f"Формат сообщения для канала: {format_type}")
    
    footer = ""
    
    await send_formatted_message(
        context,
        chat_id,
        message_text,
        format_type,
        footer,
        test_mode_enabled,
        target_chat_id
    )


async def check_channels(update: Update, context: CallbackContext) -> None:
    """
    Проверяет права бота в настроенных каналах и выводит информацию о них.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для выполнения этой команды."
        )
        return
    
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
    
    result = "📊 Информация о каналах:\n\n"
    
    for name, channel_id in channels:
        try:
            chat_info = await context.bot.get_chat(channel_id)
            bot_member = await context.bot.get_chat_member(
                chat_id=channel_id,
                user_id=context.bot.id
            )
            
            status = "✅ Доступен"
            if hasattr(bot_member, 'can_post_messages') and not bot_member.can_post_messages:
                status = "⚠️ Нет прав на отправку сообщений"
            
            result += f"{name} ({channel_id}):\n"
            result += f"Название: {chat_info.title}\n"
            result += f"Тип: {chat_info.type}\n"
            result += f"Статус: {status}\n\n"
            
        except Exception as e:
            result += f"{name} ({channel_id}):\n"
            result += f"Статус: ❌ Ошибка доступа ({str(e)})\n\n"
    
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
            
            error_message = "Извините, произошла ошибка при обработке вашего запроса."
            
            if isinstance(error, BadRequest):
                error_message = f"Ошибка запроса: {str(error)}"
            
            user_id = update.effective_user.id if update.effective_user else None
            if user_id and check_admin(user_id):
                error_message += f"\n\nДетали ошибки: {str(error)}"
                
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
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("format", format_command))
    
    application.add_handler(CommandHandler("test", test_mode))
    application.add_handler(CommandHandler("setformat", set_format))
    application.add_handler(CommandHandler("send", send_to_channel))
    application.add_handler(CommandHandler("channels", check_channels))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info("Обработчики сообщений установлены")