import logging
import os

from telegram.ext import Application

from app.bot import setup_handlers
from app.config import config
from app.utils import setup_logging

# Инициализация логирования
setup_logging()

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Setup handlers
    setup_handlers(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=list(
        [update.type for update in application.update_queue.queue])
    )


if __name__ == "__main__":
    main()