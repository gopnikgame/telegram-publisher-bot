import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Any

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters

from app.config import config
from app.utils import format_message, check_file_size

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения времени запуска
START_TIME = datetime.now()

def check_admin(func: Callable) -> Callable:
    """Декоратор для проверки прав администратора."""
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args: Any, **kwargs: Any) -> Any:
        user_id = str(update.effective_user.id)
        if user_id not in config.ADMIN_IDS:
            logger.warning(f"Попытка доступа к админ-команде от пользователя {user_id}")
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def error_handler(update: Update, context: CallbackContext) -> None:
    """Глобальный обработчик ошибок."""
    logger.error(f"Update {update} вызвал ошибку {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            error_message = "❌ Произошла ошибка при обработке запроса."
            if str(context.error):
                error_message += f"\nПодробности: {str(context.error)}"
            update.effective_message.reply_text(error_message)
    except:
        pass

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запустил бота")
    
    message = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🤖 Я бот для публикации сообщений в канале.\n"
        "📝 Отправьте мне текст или файл для публикации.\n\n"
        "Доступные команды:\n"
        "/help - показать справку\n"
    )
    
    if str(user.id) in config.ADMIN_IDS:
        message += (
            "\nКоманды администратора:\n"
            "/test - включить/выключить тестовый режим\n"
            "/format - изменить формат сообщений\n"
            "/stats - показать статистику\n"
            "/links - показать настроенные ссылки"
        )
    
    update.message.reply_text(message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help."""
    message = (
        "📖 Справка по использованию бота:\n\n"
        "1️⃣ Отправьте текст или файл для публикации\n"
        "2️⃣ Поддерживаемые форматы файлов:\n"
        "   • Документы\n"
        "   • Изображения\n"
        "   • Видео\n"
        "   • Аудио\n\n"
        "3️⃣ Форматирование текста:\n"
        "   • **жирный текст**\n"
        "   • Ссылки добавляются автоматически\n\n"
        "4️⃣ Команды:\n"
        "/start - перезапустить бота\n"
        "/help - показать эту справку\n"
    )
    
    if str(update.effective_user.id) in config.ADMIN_IDS:
        message += (
            "\n👑 Команды администратора:\n"
            "/test - тестовый режим (сообщения в тестовый чат)\n"
            "/format - изменить формат (markdown/html/plain)\n"
            "/stats - статистика использования\n"
            "/links - настроенные ссылки"
        )
    
    update.message.reply_text(message)

@check_admin
def test_mode(update: Update, context: CallbackContext) -> None:
    """Включение/выключение тестового режима."""
    try:
        new_mode = not config.TEST_MODE
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
    args = context.args
    
    if not args:
        current_format = config.DEFAULT_FORMAT
        message = (
            "📝 Доступные форматы:\n"
            "• markdown - стандартный markdown\n"
            "• html - HTML-разметка\n"
            "• plain - без форматирования\n"
            "• modern - улучшенный markdown (v2)\n\n"
            f"Текущий формат: {current_format}\n\n"
            "Для смены формата используйте:\n"
            "/format название_формата"
        )
        update.message.reply_text(message)
        return
    
    new_format = args[0].lower()
    if new_format not in ['markdown', 'html', 'plain', 'modern']:
        update.message.reply_text("❌ Неверный формат. Используйте: markdown, html, plain или modern")
        return
    
    config.DEFAULT_FORMAT = new_format
    update.message.reply_text(f"✅ Формат сообщений изменен на: {new_format}")
    logger.info(f"Формат сообщений изменен на: {new_format}")

@check_admin
def stats(update: Update, context: CallbackContext) -> None:
    """Показывает статистику бота."""
    import psutil
    
    uptime = datetime.now() - START_TIME
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Получаем информацию о процессе
    process = psutil.Process()
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=1)
    
    stats_message = (
        "📊 Статистика бота:\n\n"
        f"⏱ Время работы: {uptime.days}д {hours}ч {minutes}м {seconds}с\n"
        f"📝 Формат: {config.DEFAULT_FORMAT}\n"
        f"🔄 Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}\n"
        f"👥 Администраторов: {len(config.ADMIN_IDS)}\n"
        f"💾 Использование памяти: {memory_info.rss / 1024 / 1024:.1f} MB\n"
        f"⚡ Загрузка CPU: {cpu_percent:.1f}%"
    )
    
    update.message.reply_text(stats_message)

@check_admin
def links(update: Update, context: CallbackContext) -> None:
    """Показывает настроенные ссылки."""
    message = "🔗 Настроенные ссылки:\n\n"
    
    if config.MAIN_BOT_LINK:
        message += f"🤖 Основной бот: {config.MAIN_BOT_LINK}\n"
    
    if config.SUPPORT_BOT_LINK:
        message += f"💬 Техподдержка: {config.SUPPORT_BOT_LINK}\n"
    
    if config.CHANNEL_LINK:
        message += f"📢 Канал: {config.CHANNEL_LINK}\n"
    
    if message == "🔗 Настроенные ссылки:\n\n":
        message = "❌ Нет настроенных ссылок"
    
    update.message.reply_text(message)

def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик входящих сообщений."""
    try:
        # Определяем целевой чат
        target_chat = config.TEST_CHAT_ID if config.TEST_MODE else config.CHANNEL_ID
        if not target_chat:
            update.message.reply_text("❌ Не настроен ID канала/чата")
            return
        
        # Обрабатываем документ
        if update.message.document:
            doc = update.message.document
            try:
                check_file_size(doc.file_size)
            except Exception as e:
                update.message.reply_text(str(e))
                return
            
            # Отправляем документ
            context.bot.send_document(
                chat_id=target_chat,
                document=doc.file_id,
                caption=update.message.caption if update.message.caption else None,
                parse_mode=ParseMode.MARKDOWN if config.DEFAULT_FORMAT == 'markdown' else None
            )
        
        # Обрабатываем текстовое сообщение
        elif update.message.text:
            formatted_text = format_message(update.message.text, config.DEFAULT_FORMAT)
            
            # Отправляем сообщение
            context.bot.send_message(
                chat_id=target_chat,
                text=formatted_text,
                parse_mode=ParseMode.MARKDOWN if config.DEFAULT_FORMAT == 'markdown' else None,
                disable_web_page_preview=True
            )
        
        update.message.reply_text("✅ Сообщение успешно отправлено")
        logger.info(f"Сообщение отправлено в чат {target_chat}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        update.message.reply_text(f"❌ Ошибка при отправке сообщения: {str(e)}")

def setup_bot(dispatcher):
    """Настройка обработчиков команд бота."""
    logger.info("=== Бот инициализируется ===")
    
    # Регистрируем обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("test", test_mode))
    dispatcher.add_handler(CommandHandler("format", format_command))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("links", links))
    
    # Регистрируем обработчик сообщений
    dispatcher.add_handler(MessageHandler(
        Filters.text | Filters.document, 
        handle_message
    ))
    
    # Регистрируем обработчик ошибок
    dispatcher.add_error_handler(error_handler)
    
    logger.info("=== Обработчики команд зарегистрированы ===")