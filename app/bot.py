import logging
import os
import re
import textwrap
from datetime import datetime
from typing import Dict, Optional, List, Union

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler, Application

from .html import recreate_markdown_from_entities, markdown_to_html, modern_to_html
from .config import config

# Настройка логирования
logger = logging.getLogger(__name__)

# Словарь для хранения состояний пользователя
user_states = {}

# Константы для состояний пользователя
STATE_AWAITING_FORMAT = 'awaiting_format'
STATE_AWAITING_MESSAGE = 'awaiting_message'
STATE_NORMAL = 'normal'
STATE_TEST_MODE = 'test_mode'

# Список администраторов (ID пользователей)
# Проверяем тип данных и обрабатываем соответственно
if isinstance(config.ADMIN_IDS, str):
    # Если это строка, разбиваем по запятой
    ADMIN_IDS = [int(admin_id) for admin_id in config.ADMIN_IDS.split(',') if admin_id.strip()]
elif isinstance(config.ADMIN_IDS, list):
    # Если уже список, просто конвертируем элементы в int
    ADMIN_IDS = [int(admin_id) if isinstance(admin_id, str) else admin_id for admin_id in config.ADMIN_IDS]
else:
    # По умолчанию - пустой список
    ADMIN_IDS = []

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

def create_footer() -> str:
    """Создает подпись для сообщений."""
    footer_parts = []
    
    # Добавляем ссылку на канал
    if hasattr(config, 'CHANNEL_LINK') and config.CHANNEL_LINK and hasattr(config, 'CHANNEL_NAME') and config.CHANNEL_NAME:
        footer_parts.append(f'<a href="{config.CHANNEL_LINK}">{config.CHANNEL_NAME}</a>')
    
    # Добавляем ссылку на основной бот
    if hasattr(config, 'MAIN_BOT_LINK') and config.MAIN_BOT_LINK and hasattr(config, 'MAIN_BOT_NAME') and config.MAIN_BOT_NAME:
        footer_parts.append(f'<a href="{config.MAIN_BOT_LINK}">{config.MAIN_BOT_NAME}</a>')
    
    # Добавляем ссылку на техподдержку
    if hasattr(config, 'SUPPORT_BOT_LINK') and config.SUPPORT_BOT_LINK and hasattr(config, 'SUPPORT_BOT_NAME') and config.SUPPORT_BOT_NAME:
        footer_parts.append(f'<a href="{config.SUPPORT_BOT_LINK}">{config.SUPPORT_BOT_NAME}</a>')
    
    if footer_parts:
        return "\n" + " | ".join(footer_parts)
    return ""

async def start(update: Update, context: CallbackContext) -> None:
    """Обрабатывает команду /start."""
    chat_id = update.effective_chat.id
    
    # Создаем приветственное сообщение без HTML-тегов, кроме безопасных
    message = "👋 Привет! Я бот для форматирования текста.\n\n" \
              "Отправьте мне текст, и я помогу вам отформатировать его для Telegram.\n" \
              "Чтобы выбрать формат, используйте команду /format.\n\n" \
              "Команды:\n" \
              "/start - Показать это сообщение\n" \
              "/help - Показать справку по форматированию\n" \
              "/format - Выбрать формат сообщения"
    
    # Добавляем команды администратора для админов
    user_id = update.effective_user.id
    if check_admin(user_id):
        message += "\n\nКоманды администратора:\n" \
                  "/test - Включить/выключить тестовый режим\n" \
                  "/setformat [тип] - Установить формат по умолчанию (markdown, html, modern)"
    
    # Создаем подпись
    footer = create_footer()
    if footer:
        message += footer
    
    # Отправляем сообщение без HTML-разметки для безопасности
    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
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
    
    message = "📚 *Справка по форматированию*\n\n" \
              "*Поддерживаемые форматы:*\n" \
              "• *Markdown* - базовое форматирование текста\n" \
              "• *HTML* - продвинутое форматирование с HTML-тегами\n\n" \
              "*Примеры Markdown:*\n" \
              "• **Жирный текст** для жирного\n" \
              "• *Курсив* для курсива\n" \
              "• ~~Зачеркнутый~~ для зачеркнутого\n" \
              "• `Код` для монопространственного шрифта\n" \
              "• ```\nБлок кода\n``` для блока кода\n" \
              "• > Цитата для цитирования\n" \
              "• # Заголовок для заголовков\n" \
              "• 1. Пункт для нумерованных списков\n" \
              "• - Пункт для маркированных списков\n" \
              "• [Текст](https://example.com) для ссылок\n\n" \
              "Используйте команду /format, чтобы выбрать предпочтительный формат."
    
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
    
    logger.info(f"Администратор {user_id} {'включен' if new_state == STATE_TEST_MODE else 'выключен'} тестовый режим")

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
    if state != STATE_AWAITING_FORMAT and state != STATE_AWAITING_MESSAGE:
        format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    else:
        format_type = context.user_data.get("format", "markdown").lower()
    
    logger.info(f"Получено сообщение: {text}")
    logger.info(f"Формат сообщения: {format_type}")
    
    try:
        # Форматируем текст в зависимости от выбранного формата
        if format_type == "html":
            # Для HTML формата используем текст как есть
            formatted_text = text
        elif format_type == "modern":
            formatted_text = modern_to_html(text)
        else:  # По умолчанию используем Markdown
            formatted_text = markdown_to_html(text)
        
        logger.info(f"Отформатированное сообщение: {formatted_text}")
        
        # Определяем режим парсинга
        parse_mode = ParseMode.HTML
        logger.info(f"Режим парсинга: {parse_mode}")
        
        # Создаем подпись
        footer = create_footer()
        
        # Проверяем, находится ли пользователь в тестовом режиме
        test_mode_enabled = state == STATE_TEST_MODE
        
        # В зависимости от режима отправляем сообщение в канал или только пользователю
        if test_mode_enabled or chat_id == user_id:  # Если включен тестовый режим или это личная переписка
            # Отправляем сообщение пользователю с форматированием
            await context.bot.send_message(
                chat_id=chat_id,
                text=formatted_text,
                parse_mode=parse_mode,
                disable_web_page_preview=False
            )
        else:
            # В обычном режиме для группового чата или канала
            # Отправляем сообщение в канал
            if config.CHANNEL_ID:
                try:
                    # Если доступен тестовый чат и включен тестовый режим, отправляем туда
                    if test_mode_enabled and config.TEST_CHAT_ID:
                        target_chat_id = config.TEST_CHAT_ID
                    else:
                        target_chat_id = config.CHANNEL_ID
                    
                    # Добавляем подпись, если она доступна
                    if footer:
                        formatted_text += footer
                    
                    await context.bot.send_message(
                        chat_id=target_chat_id,
                        text=formatted_text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=False
                    )
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ Сообщение успешно отправлено в канал."
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения в канал: {str(e)}", exc_info=True)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Ошибка при отправке сообщения в канал: {str(e)}"
                    )
            else:
                # Если канал не настроен, просто отвечаем пользователю
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ ID канала не настроен. Отправьте сообщение администратору."
                )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка форматирования: {str(e)}\n\nПопробуйте другой формат или исправьте ошибки в разметке.\n\n🔍 Текст с ошибкой (для отладки):\n\n{text}"
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
    
    # Определяем, куда отправлять сообщение
    if test_mode_enabled:
        # В тестовом режиме: в TEST_CHAT_ID или себе
        if config.TEST_CHAT_ID != 0:
            target_chat_id = config.TEST_CHAT_ID
            target_name = "тестовый канал"
        else:
            target_chat_id = chat_id  # Отправляем сами себе
            target_name = "текущий чат (тестовый режим)"
    else:
        # В обычном режиме: в основной канал
        if config.CHANNEL_ID != 0:
            target_chat_id = config.CHANNEL_ID
            target_name = "основной канал"
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ ID основного канала не установлен в конфигурации."
            )
            return
    
    # Определяем формат сообщения (используем сохраненный пользователем или формат по умолчанию)
    format_type = context.user_data.get("format", context.bot_data.get("default_format", config.DEFAULT_FORMAT)).lower()
    logger.info(f"Формат сообщения для канала: {format_type}")
    
    # Форматируем текст в зависимости от выбранного формата
    if format_type == "html":
        # Для HTML формата используем текст как есть
        formatted_text = message_text
    elif format_type == "modern":
        formatted_text = modern_to_html(message_text)
    else:  # По умолчанию используем Markdown
        formatted_text = markdown_to_html(message_text)
    
    logger.info(f"Отформатированное сообщение для канала: {formatted_text}")
    
    # Добавляем подпись, если она доступна
    footer = create_footer()
    if footer:
        formatted_text += footer
    
    # Определяем режим парсинга
    parse_mode = ParseMode.HTML if format_type in ["html", "markdown", "modern"] else None
    
    # В тестовом режиме можем показать дополнительную информацию
    if test_mode_enabled:
        # Показываем отформатированный текст до отправки
        safe_preview = formatted_text.replace("<", "&lt;").replace(">", "&gt;")
        preview_message = f"📝 Предпросмотр сообщения:\n\n{safe_preview[:500]}"
        if len(safe_preview) > 500:
            preview_message += "..."
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=preview_message,
            parse_mode=None  # Без форматирования для безопасного просмотра
        )
    
    # Отправляем сообщение в целевой чат
    try:
        message = await context.bot.send_message(
            chat_id=target_chat_id,
            text=formatted_text,
            parse_mode=parse_mode,
            disable_web_page_preview=False
        )
        
        # Сообщаем об успешной отправке
        success_message = f"✅ Сообщение успешно отправлено в {target_name}."
        if test_mode_enabled:
            success_message += f"\nID сообщения: {message.message_id}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=success_message
        )
        logger.info(f"Сообщение успешно отправлено в {target_name} (ID: {target_chat_id}). ID сообщения: {message.message_id}")
    except Exception as e:
        error_message = str(e)
        logger.error(f"Ошибка при отправке сообщения в {target_name} (ID: {target_chat_id}): {error_message}", exc_info=True)
        
        # Отправляем информацию об ошибке
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка при отправке сообщения в {target_name}: {error_message}"
        )
        
        # В тестовом режиме показываем детали ошибки
        if test_mode_enabled:
            # Показываем детали для отладки
            safe_text = formatted_text.replace("<", "&lt;").replace(">", "&gt;")
            debug_info = f"🔍 Детали ошибки:\n\n" \
                        f"Целевой чат: {target_name} (ID: {target_chat_id})\n" \
                        f"Формат: {format_type}\n" \
                        f"Режим парсинга: {parse_mode}\n" \
                        f"Текст с ошибкой (часть): {safe_text[:300]}..."
            await context.bot.send_message(
                chat_id=chat_id,
                text=debug_info
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
    logger.error(msg=f"Произошла ошибка: {error}", exc_info=error)
    
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
    
    # Регистрируем обработчик для ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Обработчики сообщений установлены")