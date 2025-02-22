import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.error import TelegramError
from app.config import Config
from app.utils import escape_markdown, check_file_size, setup_logging

# Настройка логирования
logger = logging.getLogger(__name__)

class PublisherBot:
    def __init__(self):
        self.config = Config()
        self.updater = None
        setup_logging()

    def check_connection(self):
        """Проверка соединения с Telegram API."""
        try:
            response = requests.get(f'https://api.telegram.org/bot{self.config.BOT_TOKEN}/getMe')
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Соединение установлено. Бот: @{bot_info['result']['username']}")
                return True
            else:
                logger.error(f"Ошибка соединения. Код: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {e}")
            return False

    def check_channel_permissions(self, context: CallbackContext) -> bool:
        """Проверка прав бота в канале."""
        try:
            member = context.bot.get_chat_member(self.config.CHANNEL_ID, context.bot.id)
            return member.can_post_messages
        except TelegramError as e:
            logger.error(f"Ошибка при проверке прав в канале: {e}")
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором."""
        return user_id in self.config.ADMIN_IDS

    def start(self, update: Update, context: CallbackContext):
        """Обработчик команды /start."""
        try:
            user = update.effective_user
            message = (f"Привет, {user.first_name}! Отправьте сообщение или медиафайл, "
                      f"и я опубликую его в канале {self.config.CHANNEL_LINK}")
            update.message.reply_text(message)
            logger.info(f"Пользователь {user.id} запустил бота")
        except Exception as e:
            logger.error(f"Ошибка в команде start: {e}")
            update.message.reply_text("Произошла ошибка при обработке команды.")

    def handle_message(self, update: Update, context: CallbackContext):
        """Обработчик текстовых сообщений."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if not self.check_channel_permissions(context):
            update.message.reply_text("У бота нет прав для публикации в канале!")
            return

        try:
            user_message = update.message.text
            escaped_message = escape_markdown(user_message)
            response = f"{escaped_message}\n\n{self.config.create_links()}"

            context.bot.send_message(
                chat_id=self.config.CHANNEL_ID,
                text=response,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )

            update.message.reply_text("Ваше сообщение успешно опубликовано в канале!")
            logger.info(f"Опубликовано сообщение от пользователя {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при публикации сообщения: {e}")
            update.message.reply_text("Произошла ошибка при публикации сообщения.")

    def handle_media(self, update: Update, context: CallbackContext):
        """Обработчик медиафайлов."""
        if not self.is_admin(update.effective_user.id):
            update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if not self.check_channel_permissions(context):
            update.message.reply_text("У бота нет прав для публикации в канале!")
            return

        try:
            if not check_file_size(update.message):
                update.message.reply_text("Файл слишком большой! Максимальный размер: 50MB")
                return

            media_type, file_id = self._get_media_info(update.message)
            if not media_type:
                update.message.reply_text("Неподдерживаемый тип медиафайла.")
                return

            caption = update.message.caption if update.message.caption else ""
            caption = escape_markdown(caption)
            caption += self.config.create_links()

            self._send_media(context, media_type, file_id, caption, update)
            logger.info(f"Опубликован медиафайл от пользователя {update.effective_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при публикации медиафайла: {e}")
            update.message.reply_text("Произошла ошибка при публикации медиафайла.")

    def _get_media_info(self, message):
        """Получение информации о медиафайле."""
        if message.photo:
            return "photo", message.photo[-1].file_id
        elif message.video:
            return "video", message.video.file_id
        elif message.audio:
            return "audio", message.audio.file_id
        elif message.document:
            return "document", message.document.file_id
        return None, None

    def _send_media(self, context, media_type, file_id, caption, update):
        """Отправка медиафайла в канал."""
        media_methods = {
            "photo": context.bot.send_photo,
            "video": context.bot.send_video,
            "audio": context.bot.send_audio,
            "document": context.bot.send_document
        }

        method = media_methods.get(media_type)
        if method:
            method(
                chat_id=self.config.CHANNEL_ID,
                **{media_type: file_id},
                caption=caption,
                parse_mode="MarkdownV2"
            )
            update.message.reply_text("Ваш медиафайл успешно опубликован в канале!")

    def run(self):
        """Запуск бота."""
        try:
            if not self.check_connection():
                logger.error("Не удалось установить соединение с Telegram API")
                return

            self.updater = Updater(self.config.BOT_TOKEN)
            dispatcher = self.updater.dispatcher

            dispatcher.add_handler(CommandHandler("start", self.start))
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