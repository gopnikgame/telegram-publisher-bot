import logging
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, CallbackContext
)
import requests
from config import Config
from utils import setup_logging, format_message, check_file_size

logger = logging.getLogger(__name__)

class PublisherBot:
    def __init__(self):
        self.config = Config()
        self.updater = None
        setup_logging()
        self.user_formats = {}  # Словарь для хранения форматов пользователей

    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь администратором."""
        return user_id in self.config.ADMIN_IDS

    def check_connection(self) -> bool:
        """Проверка соединения с Telegram API."""
        try:
            response = requests.get(
                'https://api.telegram.org',
                proxies={'https': self.config.HTTPS_PROXY} if self.config.HTTPS_PROXY else None,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {e}")
            return False

    def check_channel_permissions(self, context: CallbackContext) -> bool:
        """Проверка прав бота в канале."""
        try:
            member = context.bot.get_chat_member(
                chat_id=self.config.CHANNEL_ID,
                user_id=context.bot.id
            )
            return member.can_post_messages
        except Exception as e:
            logger.error(f"Ошибка при проверке прав в канале: {e}")
            return False

    def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text(
                "У вас нет прав для использования этого бота."
            )
            return

        update.message.reply_text(
            "Привет! Я бот для публикации сообщений в канале.\n"
            "Отправьте мне текст или медиафайл для публикации.\n"
            "Используйте /setformat для выбора формата сообщений:\n"
            "modern - Современный формат с эмодзи\n"
            "markdown - Markdown разметка\n"
            "html - HTML разметка\n"
            "plain - Обычный текст"
        )

    def handle_message(self, update: Update, context: CallbackContext):
        """Обработчик текстовых сообщений."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if not self.check_channel_permissions(context):
            update.message.reply_text("У бота нет прав для публикации в канале!")
            return

        try:
            format_type = self.get_user_format(update.effective_user.id)
            user_message = update.message.text
            formatted_message, parse_mode = format_message(user_message, format_type)
            response = f"{formatted_message}{self.config.create_links(format_type)}"

            context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=response,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )

            update.message.reply_text(
                f"Ваше сообщение успешно опубликовано в канале! (формат: {format_type})"
            )
            logger.info(f"Опубликовано сообщение от пользователя {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
            update.message.reply_text(
                "Произошла ошибка при публикации сообщения. "
                "Проверьте форматирование и попробуйте снова."
            )

    def handle_media(self, update: Update, context: CallbackContext):
        """Обработчик медиафайлов."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if not self.check_channel_permissions(context):
            update.message.reply_text("У бота нет прав для публикации в канале!")
            return

        if not check_file_size(update.message):
            update.message.reply_text(
                "Файл слишком большой. Максимальный размер: 50MB"
            )
            return

        try:
            format_type = self.get_user_format(update.effective_user.id)
            caption = update.message.caption or ""
            formatted_caption, parse_mode = format_message(caption, format_type)
            caption_with_links = f"{formatted_caption}{self.config.create_links(format_type)}"

            if update.message.photo:
                context.bot.send_photo(
                    chat_id=self.config.CHANNEL_ID,
                    photo=update.message.photo[-1].file_id,
                    caption=caption_with_links,
                    parse_mode=parse_mode
                )
            elif update.message.video:
                context.bot.send_video(
                    chat_id=self.config.CHANNEL_ID,
                    video=update.message.video.file_id,
                    caption=caption_with_links,
                    parse_mode=parse_mode
                )
            elif update.message.audio:
                context.bot.send_audio(
                    chat_id=self.config.CHANNEL_ID,
                    audio=update.message.audio.file_id,
                    caption=caption_with_links,
                    parse_mode=parse_mode
                )
            elif update.message.document:
                context.bot.send_document(
                    chat_id=self.config.CHANNEL_ID,
                    document=update.message.document.file_id,
                    caption=caption_with_links,
                    parse_mode=parse_mode
                )

            update.message.reply_text(
                f"Ваш медиафайл успешно опубликован в канале! (формат: {format_type})"
            )
            logger.info(f"Опубликован медиафайл от пользователя {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при публикации медиафайла: {e}")
            update.message.reply_text("Произошла ошибка при публикации медиафайла.")

    def set_format(self, update: Update, context: CallbackContext):
        """Обработчик команды /setformat."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if not context.args or context.args[0].lower() not in ["markdown", "html", "plain", "modern"]:
            update.message.reply_text(
                "Пожалуйста, укажите формат: markdown, html, plain или modern\n"
                "Пример: /setformat modern"
            )
            return

        format_type = context.args[0].lower()
        self.user_formats[update.effective_user.id] = format_type
        update.message.reply_text(
            f"Формат сообщений установлен: {format_type}\n\n"
            f"{'Теперь вы можете использовать эмодзи и форматирование без экранирования' if format_type == 'modern' else 'Используйте соответствующие правила форматирования для выбранного формата'}"
        )

    def get_user_format(self, user_id: int) -> str:
        """Получение формата сообщений для пользователя."""
        return self.user_formats.get(user_id, self.config.DEFAULT_FORMAT)

    def run(self):
        """Запуск бота."""
        try:
            if not self.check_connection():
                logger.error("Не удалось установить соединение с Telegram API")
                return

            self.updater = Updater(self.config.BOT_TOKEN)
            dispatcher = self.updater.dispatcher

            dispatcher.add_handler(CommandHandler("start", self.start))
            dispatcher.add_handler(CommandHandler("setformat", self.set_format))
            dispatcher.add_handler(MessageHandler(
                Filters.text & ~Filters.command, self.handle_message))
            dispatcher.add_handler(MessageHandler(
                Filters.photo | Filters.video | Filters.audio | Filters.document,
                self.handle_media
            ))

            logger.info("Бот запущен...")
            self.updater.start_polling()
            self.updater.idle()
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise

if __name__ == "__main__":
    bot = PublisherBot()
    bot.run()