from telegram import Update, ParseMode, ChatAction
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, CallbackContext
)
from telegram.error import TelegramError
import logging
from functools import wraps
from typing import Callable, Optional
import datetime
import os

from app.config import config
from app.utils import (
    setup_logging, format_message, check_file_size,
    MessageFormattingError, FileSizeError, format_bot_links
)

# Настройка логирования
logger = setup_logging()

# Время запуска бота
START_TIME = datetime.datetime.now()

def send_typing_action(func: Callable) -> Callable:
    """Декоратор для отображения 'печатает...' во время обработки сообщения."""
    @wraps(func)
    def command_func(update: Update, context: CallbackContext, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, 
            action=ChatAction.TYPING
        )
        return func(update, context, *args, **kwargs)
    return command_func

def check_admin(func: Callable) -> Callable:
    """Декоратор для проверки прав администратора."""
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in config.ADMIN_IDS:
            update.message.reply_text('У вас нет прав для использования этой команды.')
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def error_handler(update: Update, context: CallbackContext) -> None:
    """Глобальный обработчик ошибок."""
    logger.error(f"Update {update} вызвал ошибку {context.error}")
    
    try:
        if update and update.effective_message:
            error_message = "❌ Произошла ошибка при обработке запроса."
            if str(context.error):
                error_message += f"\nПодробности: {str(context.error)}"
            update.effective_message.reply_text(error_message)
    except:
        pass

@check_admin
def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    message = (
        f"👋 Привет! Я бот для публикации сообщений в канале.\n\n"
        f"📝 Текущий формат сообщений: {config.DEFAULT_FORMAT}\n"
        f"🔄 Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}\n\n"
        f"ℹ️ Доступные команды:\n"
        f"/help - показать справку\n"
        f"/test - включить/выключить тестовый режим\n"
        f"/format - изменить формат сообщений\n"
        f"/stats - показать статистику\n"
        f"/links - показать настроенные ссылки"
    )
    update.message.reply_text(message)

@check_admin
def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help."""
    message = (
        "📚 Справка по использованию бота:\n\n"
        "1️⃣ Отправьте текст или файл для публикации\n"
        "2️⃣ Используйте команды для управления:\n"
        "/test - включить/выключить тестовый режим\n"
        "/format - изменить формат сообщений\n"
        "/stats - показать статистику\n"
        "/links - показать настроенные ссылки\n\n"
        f"ℹ️ Текущие настройки:\n"
        f"📝 Формат: {config.DEFAULT_FORMAT}\n"
        f"🔄 Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}\n\n"
        "💡 Поддерживаемые форматы:\n"
        "- **жирный текст**\n"
        "- Списки (1. пункт)\n"
        "- Эмодзи 👍\n"
        "- Ссылки https://example.com"
    )
    update.message.reply_text(message)

@check_admin
def test_mode(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /test."""
    try:
        # Переключаем режим
        new_mode = not config.TEST_MODE
        # Обновляем значение в конфиге
        config.TEST_MODE = new_mode
        
        message = (
            f"🔄 Тестовый режим {'включен' if new_mode else 'выключен'}\n"
            f"{'⚠️ Сообщения будут отправляться в тестовый чат' if new_mode else '✅ Сообщения будут отправляться в канал'}"
        )
        update.message.reply_text(message)
        
        logger.info(f"Тестовый режим {'включен' if new_mode else 'выключен'}")
    except Exception as e:
        logger.error(f"Ошибка при переключении тестового режима: {e}")
        update.message.reply_text("❌ Ошибка при переключении режима")

@check_admin
def format_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /format."""
    available_formats = ['markdown', 'html', 'plain', 'modern']
    
    if not context.args:
        current_format = config.DEFAULT_FORMAT
        message = (
            f"📝 Текущий формат: {current_format}\n\n"
            f"Доступные форматы:\n"
            f"- markdown (стандартный)\n"
            f"- html (HTML-разметка)\n"
            f"- plain (без форматирования)\n"
            f"- modern (улучшенный markdown)\n\n"
            f"Для изменения отправьте:\n"
            f"/format название_формата"
        )
        update.message.reply_text(message)
        return
    
    new_format = context.args[0].lower()
    if new_format not in available_formats:
        update.message.reply_text(
            f"❌ Неверный формат. Доступные форматы:\n"
            f"{', '.join(available_formats)}"
        )
        return
    
    try:
        # Обновляем значение в конфиге
        config.DEFAULT_FORMAT = new_format
        update.message.reply_text(f"✅ Формат сообщений изменен на: {new_format}")
        logger.info(f"Формат сообщений изменен на: {new_format}")
    except Exception as e:
        logger.error(f"Ошибка при изменении формата: {e}")
        update.message.reply_text("❌ Ошибка при изменении формата")

@check_admin
def stats(update: Update, context: CallbackContext) -> None:
    """Показывает статистику работы бота."""
    uptime = datetime.datetime.now() - START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{hours}ч {minutes}м {seconds}с"
    
    stats_message = (
        f"📊 Статистика бота:\n\n"
        f"⏱️ Время работы: {uptime_str}\n"
        f"🔄 Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}\n"
        f"📝 Формат сообщений: {config.DEFAULT_FORMAT}\n"
        f"📨 Максимальный размер файла: {config.MAX_FILE_SIZE / 1024 / 1024:.1f} MB"
    )
    update.message.reply_text(stats_message)

@check_admin
def links(update: Update, context: CallbackContext) -> None:
    """Показывает настроенные ссылки."""
    links_info = format_bot_links(config.DEFAULT_FORMAT)
    message = f"🔗 Настроенные ссылки:\n\n{links_info}"
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

@check_admin
@send_typing_action
def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик входящих сообщений."""
    try:
        message = update.message
        
        # Определяем режим парсинга на основе формата
        parse_mode = {
            'markdown': ParseMode.MARKDOWN,
            'html': ParseMode.HTML,
            'modern': ParseMode.MARKDOWN_V2,
            'plain': None
        }.get(config.DEFAULT_FORMAT.lower())
        
        # Определяем целевой чат
        target_chat_id = (config.TEST_CHAT_ID or str(update.effective_user.id)) if config.TEST_MODE else config.CHANNEL_ID
        test_prefix = "[ТЕСТ] " if config.TEST_MODE else ""
        
        if message.document:
            # Проверка размера файла
            check_file_size(message.document.file_size)
            
            # Получаем описание файла
            caption = message.caption or ''
            formatted_caption = format_message(f"{test_prefix}{caption}", config.DEFAULT_FORMAT)
            
            # Отправляем файл
            sent_message = context.bot.send_document(
                chat_id=target_chat_id,
                document=message.document.file_id,
                caption=formatted_caption,
                parse_mode=parse_mode
            )
        else:
            # Форматируем и отправляем текстовое сообщение
            formatted_text = format_message(f"{test_prefix}{message.text}", config.DEFAULT_FORMAT)
            sent_message = context.bot.send_message(
                chat_id=target_chat_id,
                text=formatted_text,
                parse_mode=parse_mode
            )
        
        # Логируем успешную отправку
        logger.info(
            f"Сообщение отправлено в чат {target_chat_id} "
            f"(тестовый режим: {config.TEST_MODE})"
        )
        
        update.message.reply_text("✅ Сообщение отправлено")
        
    except FileSizeError as e:
        update.message.reply_text(f"❌ {str(e)}")
        logger.warning(f"Ошибка размера файла: {e}")
    except MessageFormattingError as e:
        update.message.reply_text(f"❌ {str(e)}")
        logger.error(f"Ошибка форматирования: {e}")
    except TelegramError as e:
        error_message = f"❌ Ошибка Telegram: {str(e)}"
        logger.error(error_message)
        update.message.reply_text(error_message)
    except Exception as e:
        error_message = f"❌ Неизвестная ошибка: {str(e)}"
        logger.error(error_message)
        update.message.reply_text(error_message)

def main() -> None:
    """Основная функция запуска бота."""
    try:
        updater = Updater(config.BOT_TOKEN)
        dispatcher = updater.dispatcher
        
        # Регистрация обработчиков команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("test", test_mode))
        dispatcher.add_handler(CommandHandler("format", format_command))
        dispatcher.add_handler(CommandHandler("stats", stats))
        dispatcher.add_handler(CommandHandler("links", links))
        
        # Регистрация обработчика сообщений
        dispatcher.add_handler(MessageHandler(
            Filters.text | Filters.document, 
            handle_message
        ))
        
        # Регистрация обработчика ошибок
        dispatcher.add_error_handler(error_handler)
        
        # Запуск бота
        if config.HTTPS_PROXY:
            updater.start_polling(
                bootstrap_retries=-1,
                read_timeout=30,
                connect_timeout=15,
                request_kwargs={
                    'proxy_url': config.HTTPS_PROXY
                }
            )
        else:
            updater.start_polling()
        
        logger.info('Бот успешно запущен')
        updater.idle()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        raise