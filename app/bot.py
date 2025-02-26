import logging
from functools import wraps
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application,
)
from app.config import config
from app.utils import format_message, setup_logging

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

def check_admin(func):
    """Декоратор для проверки прав администратора."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.ADMIN_IDS:
            logger.warning(f"Попытка несанкционированного доступа от пользователя {user_id}")
            await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def test_mode(func):
    """Декоратор для обработки тестового режима."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Проверяем, включен ли тестовый режим
        is_test = context.user_data.get('test_mode', config.TEST_MODE)
        
        # Если тестовый режим включен, но TEST_CHAT_ID не настроен
        if is_test and not config.TEST_CHAT_ID:
            await update.message.reply_text("⚠️ Тестовый режим включен, но TEST_CHAT_ID не настроен")
            return
        
        # Добавляем информацию о тестовом режиме в context
        context.user_data['is_test'] = is_test
        context.user_data['target_chat'] = config.TEST_CHAT_ID if is_test else config.CHANNEL_ID
        
        return await func(update, context, *args, **kwargs)
    return wrapped

@check_admin
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text(
        "👋 Привет! Я бот для публикации сообщений в канал.\n\n"
        "Отправьте мне текст или файл для публикации.\n"
        f"Текущий формат: {config.DEFAULT_FORMAT}\n"
        f"Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}"
    )

@check_admin
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text(
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
async def set_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /format."""
    if not context.args:
        await update.message.reply_text("❌ Укажите формат: markdown, html, modern или plain")
        return
    format_type = context.args[0].lower()
    if format_type not in ['markdown', 'html', 'modern', 'plain']:
        await update.message.reply_text("❌ Неверный формат")
        return
    context.user_data['format'] = format_type
    await update.message.reply_text(f"✅ Установлен формат: {format_type}")

@check_admin
async def toggle_test_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /test."""
    if not context.args:
        await update.message.reply_text("❌ Укажите on или off")
        return
    mode = context.args[0].lower()
    if mode not in ['on', 'off']:
        await update.message.reply_text("❌ Неверное значение")
        return
    if mode == 'on' and not config.TEST_CHAT_ID:
        await update.message.reply_text("❌ TEST_CHAT_ID не настроен в конфигурации")
        return
    context.user_data['test_mode'] = (mode == 'on')
    await update.message.reply_text(
        f"✅ Тестовый режим: {'включен' if mode == 'on' else 'выключен'}\n"
        f"{'Сообщения будут отправляться в тестовый чат' if mode == 'on' else 'Сообщения будут публиковаться в канал'}"
    )

@check_admin
@test_mode
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик входящих сообщений."""
    try:
        logger.info(f"Получено сообщение: {update.message.text}")  # Логируем входящее сообщение
        # Определяем формат сообщения
        format_type = context.user_data.get('format', config.DEFAULT_FORMAT)
        logger.info(f"Формат сообщения: {format_type}")  # Логируем формат
        # Получаем целевой чат из декоратора test_mode
        target_chat = context.user_data['target_chat']
        is_test = context.user_data['is_test']
        # Форматируем сообщение
        formatted_text = format_message(update.message.text, format_type)
        logger.info(f"Отформатированное сообщение: {formatted_text}")  # Логируем отформатированное сообщение
        # Определяем режим форматирования для Telegram
        parse_mode = None
        if format_type == 'html':
            parse_mode = ParseMode.HTML
        elif format_type in ['markdown', 'modern']:
            parse_mode = ParseMode.MARKDOWN_V2
        logger.info(f"Режим парсинга: {parse_mode}")  # Логируем режим парсинга
        # Отправляем сообщение
        sent_message = await context.bot.send_message(
            chat_id=target_chat,
            text=formatted_text,
            parse_mode=parse_mode
        )
        logger.info(f"Сообщение отправлено: {sent_message.message_id}")  # Логируем ID отправленного сообщения
        # Отправляем подтверждение с информацией о режиме
        await update.message.reply_text(
            f"✅ Сообщение {'протестировано' if is_test else 'опубликовано'}!"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

def setup_handlers(application: Application) -> None:
    """Настройка обработчиков команд бота."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("format", set_format))
    application.add_handler(CommandHandler("test", toggle_test_mode))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот настроен и готов к работе")