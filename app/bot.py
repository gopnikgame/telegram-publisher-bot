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

from app.config import config  # Импортируем экземпляр конфигурации
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
    """Обработчик ошибок бота."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if isinstance(context.error, MessageFormattingError):
        update.message.reply_text(
            f"❌ Ошибка форматирования сообщения:\n{str(context.error)}"
        )
    elif isinstance(context.error, FileSizeError):
        update.message.reply_text(
            f"❌ Ошибка с файлом:\n{str(context.error)}"
        )
    elif isinstance(context.error, TelegramError):
        update.message.reply_text(
            f"❌ Ошибка Telegram API:\n{str(context.error)}"
        )
    else:
        update.message.reply_text(
            "❌ Произошла непредвиденная ошибка. Администратор уведомлен."
        )

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
        f"🔄 Тестовый режим: {'включен' if config.TEST_MODE else 'выключен'}"
    )
    update.message.reply_text(message)
    
@check_admin
def test_mode(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /test."""
    try:
        new_mode = not config.TEST_MODE
        os.environ['TEST_MODE'] = str(new_mode).lower()
        config.TEST_MODE = new_mode
        
        message = (
            f"🔄 Тестовый режим {'включен' if new_mode else 'выключен'}\n"
            f"{'⚠️ Сообщения будут отправляться в тестовый чат' if new_mode else '✅ Сообщения будут отправляться в канал'}"
        )
        update.message.reply_text(message)
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
        os.environ['DEFAULT_FORMAT'] = new_format
        config.DEFAULT_FORMAT = new_format
        update.message.reply_text(f"✅ Формат сообщений изменен на: {new_format}")
    except Exception as e:
        logger.error(f"Ошибка при изменении формата: {e}")
        update.message.reply_text("❌ Ошибка при изменении формата")

@check_admin
@send_typing_action
def status(update: Update, context: CallbackContext) -> None:
    """Показывает текущий статус бота."""
    try:
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        
        status_text = f"""
*Статус бота:*

🖥 *Система:*
CPU: {cpu_usage}%
RAM: {memory.percent}%
Диск: {disk.percent}%
Аптайм: {str(uptime).split('.')[0]}

⚙️ *Конфигурация:*
Канал: {Config.CHANNEL_ID}
Формат: {Config.DEFAULT_FORMAT}
Макс. размер файла: {Config.MAX_FILE_SIZE/1024/1024}MB
Тестовый режим: {'Включен ✅' if Config.TEST_MODE else 'Выключен ❌'}

📊 *Рабочая директория:*
{os.getcwd()}
"""
        update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Ошибка при получении статуса: {e}")
        update.message.reply_text(f"❌ Ошибка при получении статуса: {str(e)}")

@check_admin
def stats(update: Update, context: CallbackContext) -> None:
    """Показывает статистику работы бота."""
    uptime = datetime.datetime.now() - START_TIME
    stats_message = (
        f"📊 Статистика бота:\n\n"
        f"⏱️ Время работы: {uptime}\n"
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
def settings(update: Update, context: CallbackContext) -> None:
    """Показывает текущие настройки бота."""
    from app.utils import format_bot_links
    
    try:
        settings_text = f"""
*Текущие настройки:*

📝 *Форматирование:*
Формат по умолчанию: {Config.DEFAULT_FORMAT}
Максимальный размер файла: {Config.MAX_FILE_SIZE/1024/1024}MB
Тестовый режим: {'Включен ✅' if Config.TEST_MODE else 'Выключен ❌'}

🔗 *Ссылки:*
{format_bot_links(Config.DEFAULT_FORMAT)}

👥 *Доступ:*
Администраторы: {', '.join(Config.ADMIN_IDS)}
ID канала: {Config.CHANNEL_ID}

🌐 *Прокси:*
HTTPS прокси: {Config.HTTPS_PROXY or "Не используется"}
"""
        update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Ошибка при отправке настроек: {e}")
        update.message.reply_text(
            "Ошибка форматирования. Отправляю без разметки:\n\n" + 
            settings_text.replace('*', '')
        )
        
@check_admin
def set_format(update: Update, context: CallbackContext) -> None:
    """Устанавливает формат сообщений."""
    if not context.args:
        update.message.reply_text(
            'Укажите формат: /setformat <markdown/html/plain/modern>'
        )
        return
    
    new_format = context.args[0].lower()
    if new_format not in ['markdown', 'html', 'plain', 'modern']:
        update.message.reply_text(
            'Неверный формат. Допустимые значения: markdown, html, plain, modern'
        )
        return
    
    # В реальном приложении здесь должно быть сохранение настройки в базу данных
    Config.DEFAULT_FORMAT = new_format
    update.message.reply_text(f'Формат сообщений установлен: {new_format}')

@check_admin
def format_help(update: Update, context: CallbackContext) -> None:
    """Показывает примеры форматирования."""
    format_text = """
*Примеры форматирования:*

1️⃣ *Modern (по умолчанию):*
```
🌟 **Заголовок** 🌟
Обычный текст
📌 **Важно:**
1. Первый пункт
2. Второй пункт
```

2️⃣ *Markdown:*
```
*Жирный текст*
_Курсив_
[Ссылка](http://example.com)
```

3️⃣ *HTML:*
```
<b>Жирный текст</b>
<i>Курсив</i>
<a href="http://example.com">Ссылка</a>
```

4️⃣ *Plain:*
```
Обычный текст без форматирования
```
"""
    update.message.reply_text(format_text, parse_mode=ParseMode.MARKDOWN)

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
            'modern': ParseMode.MARKDOWN,
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
            context.bot.send_document(
                chat_id=target_chat_id,
                document=message.document.file_id,
                caption=formatted_caption,
                parse_mode=parse_mode
            )
        else:
            # Форматируем и отправляем текстовое сообщение
            formatted_text = format_message(f"{test_prefix}{message.text}", config.DEFAULT_FORMAT)
            context.bot.send_message(
                chat_id=target_chat_id,
                text=formatted_text,
                parse_mode=parse_mode
            )
        
        update.message.reply_text("✅ Сообщение отправлено")
        
    except FileSizeError as e:
        update.message.reply_text(f"❌ {str(e)}")
    except MessageFormattingError as e:
        update.message.reply_text(f"❌ {str(e)}")
    except TelegramError as e:
        error_message = f"❌ Ошибка Telegram: {str(e)}"
        logger.error(error_message)
        update.message.reply_text(error_message)
    except Exception as e:
        error_message = f"❌ Неизвестная ошибка: {str(e)}"
        logger.error(error_message)
        update.message.reply_text(error_message)

@check_admin
def toggle_test_mode(update: Update, context: CallbackContext) -> None:
    """Включает/выключает тестовый режим."""
    try:
        Config.TEST_MODE = not Config.TEST_MODE
        mode_status = "включен ✅" if Config.TEST_MODE else "выключен ❌"
        target = f"ID {Config.TEST_CHAT_ID}" if Config.TEST_CHAT_ID else "текущий чат"
        
        update.message.reply_text(
            f"🔄 Тестовый режим {mode_status}\n"
            f"📨 Сообщения будут отправляться в {target}"
        )
    except Exception as e:
        logger.error(f"Ошибка при переключении тестового режима: {e}")
        update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

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

if __name__ == '__main__':
    main()