from app.config import Config
import logging
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, CallbackContext
)
import requests
from app.utils import setup_logging, format_message, check_file_size

# Настройка логирования
logger = setup_logging()

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    if str(user_id) in Config.ADMIN_IDS:
        update.message.reply_text(
            'Привет! Я бот для публикации сообщений. '
            'Отправь мне текст или медиафайл для публикации в канале.'
        )
    else:
        update.message.reply_text('У вас нет прав для использования этого бота.')

def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработчик входящих сообщений."""
    user_id = update.effective_user.id
    if str(user_id) not in Config.ADMIN_IDS:
        update.message.reply_text('У вас нет прав для использования этого бота.')
        return

    try:
        message = update.message
        if message.text:
            # Обработка текстового сообщения
            formatted_text = format_message(message.text)
            context.bot.send_message(
                chat_id=Config.CHANNEL_ID,
                text=formatted_text,
                parse_mode=Config.DEFAULT_FORMAT
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
                parse_mode=Config.DEFAULT_FORMAT
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
                parse_mode=Config.DEFAULT_FORMAT
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
                parse_mode=Config.DEFAULT_FORMAT
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

        # Регистрация обработчиков
        dispatcher.add_handler(CommandHandler("start", start))
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