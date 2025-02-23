from app.config import Config
import logging
from telegram import Update, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, CallbackContext
)
import requests
from app.utils import setup_logging, format_message, check_file_size
import psutil
import os
import datetime

# Настройка логирования
logger = setup_logging()

def check_admin(func):
    """Декоратор для проверки прав администратора."""
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in Config.ADMIN_IDS:
            update.message.reply_text('У вас нет прав для использования этой команды.')
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    if str(user_id) in Config.ADMIN_IDS:
        commands_help = """
*Доступные команды:*

📝 Основные команды:
/start - Начать работу с ботом
/help - Показать это сообщение
        
📊 Статистика и информация:
/status - Показать статус бота
/stats - Показать статистику использования
        
⚙️ Управление:
/settings - Настройки бота
/restart - Перезапустить бота
/update - Обновить настройки из .env
        
📋 Форматирование:
/format - Показать примеры форматирования
/setformat <тип> - Установить формат сообщений (markdown/html/plain/modern)
"""
        update.message.reply_text(
            commands_help,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text('У вас нет прав для использования этого бота.')

@check_admin
def status(update: Update, context: CallbackContext) -> None:
    """Показывает текущий статус бота."""
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

📊 *Рабочая директория:*
{os.getcwd()}
"""
    update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)

@check_admin
def stats(update: Update, context: CallbackContext) -> None:
    """Показывает статистику использования бота."""
    # Здесь можно добавить подсчет сообщений из лог-файла
    stats_text = """
*Статистика использования:*

📊 *Сегодня:*
Отправлено сообщений: [В разработке]
Обработано медиафайлов: [В разработке]
Ошибок: [В разработке]

📈 *Всего:*
Отправлено сообщений: [В разработке]
Обработано медиафайлов: [В разработке]
Ошибок: [В разработке]
"""
    update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

@check_admin
def settings(update: Update, context: CallbackContext) -> None:
    """Показывает текущие настройки бота."""
    settings_text = f"""
*Текущие настройки:*

📝 *Форматирование:*
Формат по умолчанию: {Config.DEFAULT_FORMAT}
Максимальный размер файла: {Config.MAX_FILE_SIZE/1024/1024}MB

🔗 *Ссылки:*
Основной бот: {Config.MAIN_BOT_LINK}
Поддержка: {Config.SUPPORT_BOT_LINK}
Канал: {Config.CHANNEL_LINK}

👥 *Доступ:*
Администраторы: {', '.join(Config.ADMIN_IDS)}
ID канала: {Config.CHANNEL_ID}

🌐 *Прокси:*
HTTPS прокси: {Config.HTTPS_PROXY or "Не используется"}
"""
    update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)

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
    
    # Здесь можно добавить сохранение формата в .env файл
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

def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик входящих сообщений."""
    user_id = update.effective_user.id
    if str(user_id) not in Config.ADMIN_IDS:
        update.message.reply_text('У вас нет прав для использования этого бота.')
        return

    try:
        message = update.message
        # Исправляем определение parse_mode
        if Config.DEFAULT_FORMAT.lower() == 'markdown':
            parse_mode = ParseMode.MARKDOWN
        elif Config.DEFAULT_FORMAT.lower() == 'html':
            parse_mode = ParseMode.HTML
        else:
            parse_mode = None

        if message.text:
            # Обработка текстового сообщения
            formatted_text = format_message(message.text)
            context.bot.send_message(
                chat_id=Config.CHANNEL_ID,
                text=formatted_text,
                parse_mode=parse_mode
            )
        elif message.photo:
            # Обработка фото
            photo = message.photo[-1]
            if not check_file_size(photo.file_size):
                update.message.reply_text('Файл слишком большой.')
                return
            caption = format_message(message.caption) if message.caption else ''
            context.bot.send_photo(
                chat_id=Config.CHANNEL_ID,
                photo=photo.file_id,
                caption=caption,
                parse_mode=parse_mode
            )
        elif message.video:
            # Обработка видео
            if not check_file_size(message.video.file_size):
                update.message.reply_text('Файл слишком большой.')
                return
            caption = format_message(message.caption) if message.caption else ''
            context.bot.send_video(
                chat_id=Config.CHANNEL_ID,
                video=message.video.file_id,
                caption=caption,
                parse_mode=parse_mode
            )
        elif message.document:
            # Обработка документов
            if not check_file_size(message.document.file_size):
                update.message.reply_text('Файл слишком большой.')
                return
            caption = format_message(message.caption) if message.caption else ''
            context.bot.send_document(
                chat_id=Config.CHANNEL_ID,
                document=message.document.file_id,
                caption=caption,
                parse_mode=parse_mode
            )
        update.message.reply_text('Сообщение успешно опубликовано!')
    except Exception as e:
        logger.error(f'Ошибка при публикации сообщения: {e}')
        update.message.reply_text('Произошла ошибка при публикации сообщения.')

def main() -> None:
    """Основная функция бота."""
    try:
        updater = Updater(Config.BOT_TOKEN)
        dispatcher = updater.dispatcher

        # Регистрация обработчиков команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", start))
        dispatcher.add_handler(CommandHandler("status", status))
        dispatcher.add_handler(CommandHandler("stats", stats))
        dispatcher.add_handler(CommandHandler("settings", settings))
        dispatcher.add_handler(CommandHandler("format", format_help))
        dispatcher.add_handler(CommandHandler("setformat", set_format))
        
        # Обработчик сообщений
        dispatcher.add_handler(MessageHandler(
            Filters.text | Filters.photo | Filters.video | Filters.document, 
            handle_message
        ))

        # Запуск бота
        if Config.HTTPS_PROXY:
            updater.start_polling(
                bootstrap_retries=-1,
                read_timeout=30,
                connect_timeout=15,
                request_kwargs={
                    'proxy_url': Config.HTTPS_PROXY
                }
            )
        else:
            updater.start_polling()

        logger.info('Бот запущен')
        updater.idle()
    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {e}')

if __name__ == '__main__':
    main()