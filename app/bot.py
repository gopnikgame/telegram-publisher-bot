from functools import wraps
from telegram import Update, ParseMode
from telegram.ext import (
    Updater, 
    CommandHandler, 
    MessageHandler, 
    Filters, 
    CallbackContext
)
from app.config import config
from app.utils import format_message
import logging

logger = logging.getLogger(__name__)

def check_admin(func):
    """Декоратор для проверки прав администратора."""
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.ADMIN_IDS:
            logger.warning(f"Попытка несанкционированного доступа от пользователя {user_id}")
            update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def test_mode(func):
    """Декоратор для обработки тестового режима."""
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        # Проверяем, включен ли тестовый режим
        is_test = context.user_data.get('test_mode', config.TEST_MODE)
        
        # Если тестовый режим включен, но TEST_CHAT_ID не настроен
        if is_test and not config.TEST_CHAT_ID:
            update.message.reply_text("⚠️ Тестовый режим включен, но TEST_CHAT_ID не настроен")
            return
        
        # Добавляем информацию о тестовом режиме в context
        context.user_data['is_test'] = is_test
        context.user_data['target_chat'] = config.TEST_CHAT_ID if is_test else config.CHANNEL_ID
        
        return func(update, context, *args, **kwargs)
    return wrapped

@check_admin
def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    update.message.reply_text(
        "👋 Привет! Я бот для публикации сообщений в канал.\n\n"
        "Отправьте мне текст или файл для публикации.\n"
        f"Текущий формат: {config.DEFAULT_FORMAT}\n"
        f"Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}"
    )

@check_admin
def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help."""
    update.message.reply_text(
        "📝 Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Показать это сообщение\n"
        "/format <тип> - Изменить формат (markdown/html/modern/plain)\n"
        "/test <on/off> - Включить/выключить тестовый режим\n\n"
        "Поддерживаемые форматы:\n"
        "• markdown - Стандартный Markdown\n"
        "• html - HTML разметка\n"
        "• modern - Discord-подобная разметка\n"
        "• plain - Без форматирования\n\n"
        "Тестовый режим:\n"
        "• /test on - Включить тестовый режим (сообщения будут отправляться в тестовый чат)\n"
        "• /test off - Выключить тестовый режим (сообщения будут публиковаться в канал)"
    )

@check_admin
def set_format(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /format."""
    if not context.args:
        update.message.reply_text("❌ Укажите формат: markdown, html, modern или plain")
        return

    format_type = context.args[0].lower()
    if format_type not in ['markdown', 'html', 'modern', 'plain']:
        update.message.reply_text("❌ Неверный формат")
        return

    context.user_data['format'] = format_type
    update.message.reply_text(f"✅ Установлен формат: {format_type}")

@check_admin
def toggle_test_mode(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /test."""
    if not context.args:
        update.message.reply_text("❌ Укажите on или off")
        return

    mode = context.args[0].lower()
    if mode not in ['on', 'off']:
        update.message.reply_text("❌ Неверное значение")
        return

    if mode == 'on' and not config.TEST_CHAT_ID:
        update.message.reply_text("❌ TEST_CHAT_ID не настроен в конфигурации")
        return

    context.user_data['test_mode'] = (mode == 'on')
    update.message.reply_text(
        f"✅ Тестовый режим {'включен' if mode == 'on' else 'выключен'}\n"
        f"{'Сообщения будут отправляться в тестовый чат' if mode == 'on' else 'Сообщения будут публиковаться в канал'}"
    )

@check_admin
@test_mode
def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик входящих сообщений."""
    try:
        # Определяем формат сообщения
        format_type = context.user_data.get('format', config.DEFAULT_FORMAT)
        
        # Получаем целевой чат из декоратора test_mode
        target_chat = context.user_data['target_chat']
        is_test = context.user_data['is_test']
        
        # Форматируем сообщение
        formatted_text = format_message(update.message.text, format_type)
        
        # Определяем режим форматирования для Telegram
        parse_mode = None
        if format_type == 'html':
            parse_mode = ParseMode.HTML
        elif format_type in ['markdown', 'modern']:
            parse_mode = ParseMode.MARKDOWN_V2
        
        # Отправляем сообщение
        sent_message = context.bot.send_message(
            chat_id=target_chat,
            text=formatted_text,
            parse_mode=parse_mode
        )
        
        # Отправляем подтверждение с информацией о режиме
        update.message.reply_text(
            f"✅ Сообщение {'протестировано' if is_test else 'опубликовано'}!"
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)
        update.message.reply_text(f"❌ Ошибка: {str(e)}")

def setup_bot(dp):
    """Настройка обработчиков команд бота."""
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("format", set_format))
    dp.add_handler(CommandHandler("test", toggle_test_mode))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    logger.info("Бот настроен и готов к работе")