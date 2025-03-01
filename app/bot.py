import logging
import os
import re
import textwrap
from datetime import datetime
from typing import Dict, Optional, List, Union

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
# Правильный импорт ParseMode из нового местоположения
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
    
    # Безопасно проверяем наличие атрибутов в объекте config
    if hasattr(config, 'PUBLIC_CHANNEL_LINK') and config.PUBLIC_CHANNEL_LINK:
        footer_parts.append(f'<a href="{config.PUBLIC_CHANNEL_LINK}">PUBLIC</a>')
    
    if hasattr(config, 'BOT_LINK') and config.BOT_LINK:
        footer_parts.append(f'<a href="{config.BOT_LINK}">Bot_VPNLine</a>')
    
    if hasattr(config, 'SUPPORT_LINK') and config.SUPPORT_LINK:
        footer_parts.append(f'<a href="{config.SUPPORT_LINK}">SUPPORT</a>')
    
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
    
    # Создаем клавиатуру с вариантами форматирования
    keyboard = [
        [
            InlineKeyboardButton("Markdown", callback_data="format_markdown"),
            InlineKeyboardButton("HTML", callback_data="format_html")
        ],
        [
            InlineKeyboardButton("Modern", callback_data="format_modern")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение с кнопками
    await context.bot.send_message(
        chat_id=chat_id,
        text="Выберите предпочтительный формат для обработки текста:",
        reply_markup=reply_markup
    )


async def set_format(update: Update, context: CallbackContext) -> None:
    """
    Устанавливает формат по умолчанию (команда только для администраторов).
    Использование: /setformat markdown|html|modern
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверяем, является ли пользователь администратором
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для использования этой команды."
        )
        return
    
    # Проверяем аргументы команды
    if not context.args or len(context.args) < 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Укажите формат: /setformat markdown|html|modern"
        )
        return
    
    # Получаем формат из аргумента
    format_type = context.args[0].lower()
    
    # Проверяем, правильный ли формат
    if format_type not in ["markdown", "html", "modern"]:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Неверный формат. Доступные варианты: markdown, html, modern"
        )
        return
    
    # Устанавливаем формат по умолчанию
    context.bot_data["default_format"] = format_type
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Формат по умолчанию установлен: {format_type}"
    )
    logger.info(f"Администратор {user_id} установил формат по умолчанию: {format_type}")


async def test_mode(update: Update, context: CallbackContext) -> None:
    """
    Включает/выключает тестовый режим (команда только для администраторов).
    В тестовом режиме бот показывает промежуточные результаты форматирования.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Проверяем, является ли пользователь администратором
    if not check_admin(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ У вас нет прав для использования этой команды."
        )
        return
    
    # Проверяем текущее состояние тестового режима
    test_mode_enabled = context.bot_data.get("test_mode", False)
    
    # Меняем состояние на противоположное
    context.bot_data["test_mode"] = not test_mode_enabled
    
    status = "включен" if not test_mode_enabled else "выключен"
    
    # Устанавливаем тестовый режим для пользователя
    if not test_mode_enabled:
        user_states[user_id] = STATE_TEST_MODE
    else:
        user_states[user_id] = STATE_NORMAL
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Тестовый режим {status}."
    )
    logger.info(f"Администратор {user_id} {status} тестовый режим")


async def button_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает нажатия на кнопки."""
    query = update.callback_query
    chat_id = query.message.chat_id
    
    # Отвечаем на запрос, чтобы убрать часы загрузки
    await query.answer()
    
    # Получаем данные из callback_data
    callback_data = query.data
    
    # Обработка выбора формата
    if callback_data.startswith("format_"):
        format_type = callback_data.replace("format_", "")
        
        # Сохраняем выбранный формат в пользовательских данных
        context.user_data["format"] = format_type
        
        # Обновляем сообщение с кнопками
        await query.edit_message_text(
            text=f"Выбранный формат: {format_type.upper()}\n\n"
                 f"Отправьте мне текст для форматирования."
        )
        
        # Устанавливаем состояние ожидания сообщения
        user_states[chat_id] = STATE_AWAITING_MESSAGE


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обрабатывает входящие сообщения."""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message = update.message
        
        if message and message.text:
            # Восстанавливаем исходный текст с маркерами форматирования
            raw_text = message.text
            entities = message.entities or []
            
            if entities:
                # Если есть форматирование, восстанавливаем маркеры форматирования
                try:
                    raw_text = recreate_markdown_from_entities(raw_text, entities)
                except Exception as e:
                    logger.error(f"Ошибка при восстановлении маркеров форматирования: {str(e)}", exc_info=True)
            
            logger.info(f"Получено сообщение: {raw_text}")
            
            # Определяем формат сообщения (используем сохраненный пользователем или формат по умолчанию)
            format_type = context.user_data.get("format", context.bot_data.get("default_format", "markdown")).lower()
            logger.info(f"Формат сообщения: {format_type}")
            
            # Если активен тестовый режим и пользователь администратор, показываем исходный текст
            test_mode_enabled = context.bot_data.get("test_mode", False)
            is_in_test_mode = user_states.get(user_id) == STATE_TEST_MODE
            
            if test_mode_enabled and check_admin(user_id) and is_in_test_mode:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📋 Исходный текст с маркерами:\n\n{raw_text}"
                )
            
            # Форматируем текст в зависимости от выбранного формата
            if format_type == "html":
                # Для HTML формата используем текст как есть
                formatted_text = raw_text
            elif format_type == "modern":
                formatted_text = modern_to_html(raw_text)
            else:  # По умолчанию используем Markdown
                formatted_text = markdown_to_html(raw_text)
            
            logger.info(f"Отформатированное сообщение: {formatted_text}")
            
            # В тестовом режиме показываем отформатированный HTML до добавления подписи
            if test_mode_enabled and check_admin(user_id) and is_in_test_mode:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🔄 Отформатированный текст (HTML):\n\n{formatted_text}"
                )
            
            # Добавляем подпись, если она доступна
            footer = create_footer()
            if footer:
                formatted_text += footer
            
            # Определяем режим парсинга
            parse_mode = ParseMode.HTML if format_type in ["html", "markdown", "modern"] else None
            logger.info(f"Режим парсинга: {parse_mode}")
            
            # Отправляем отформатированный текст
            try:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    parse_mode=parse_mode
                )
                logger.info(f"Сообщение успешно отправлено с ID: {sent_message.message_id}")
            except BadRequest as e:
                logger.error(f"Ошибка при отправке сообщения: {str(e)}", exc_info=True)
                # Если не удалось отправить с HTML-форматированием, пробуем без него
                if "can't parse entities" in str(e).lower():
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Ошибка форматирования: {str(e)}\n\nПопробуйте другой формат или исправьте ошибки в разметке."
                    )
                    
                    # В тестовом режиме отправляем содержимое с ошибкой для отладки
                    if test_mode_enabled and check_admin(user_id) and is_in_test_mode:
                        # Экранируем HTML для безопасного отображения
                        safe_text = formatted_text.replace("<", "&lt;").replace(">", "&gt;")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"🔍 Текст с ошибкой (для отладки):\n\n{safe_text}",
                            parse_mode=ParseMode.HTML
                        )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Произошла ошибка при обработке сообщения: {str(e)}"
            )
        except:
            logger.error("Не удалось отправить сообщение об ошибке", exc_info=True)


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ошибки."""
    logger.error(msg="Произошла ошибка:", exc_info=context.error)
    
    try:
        if update and update.effective_chat:
            chat_id = update.effective_chat.id
            await context.bot.send_message(
                chat_id=chat_id,
                text="Извините, произошла ошибка при обработке вашего запроса."
            )
    except:
        logger.error("Не удалось отправить сообщение об ошибке", exc_info=True)


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
    
    # Регистрируем обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Регистрируем обработчик для обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик для ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Обработчики сообщений установлены")