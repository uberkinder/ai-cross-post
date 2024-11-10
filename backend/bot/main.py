from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import sys
import logging
from datetime import datetime

# Добавляем путь к backend/app в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.db_service import DatabaseService

# Настройка логирования
os.makedirs('logs/bot', exist_ok=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

db = DatabaseService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start"""
    logger.info(f"Received /start command from user {update.effective_user.id}")
    if not update.message:
        return

    # Извлекаем токен из команды /start, если он есть
    args = context.args
    if args:
        token = args[0]
        logger.info(f"Start command contains token: {token}")
        # Здесь можно добавить логику обработки токена
    
    await update.message.reply_text(
        "Bot is ready to monitor channels. "
        "Make sure to add me as an administrator to your channel."
    )

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка новых постов в каналах"""
    logger.info("Received channel post update")
    message = update.channel_post or update.edited_channel_post
    if not message:
        logger.warning("No message in update")
        return

    channel_id = message.chat_id
    message_id = message.message_id
    chat_type = message.chat.type
    
    logger.info(f"""
    Received post:
    Channel ID: {channel_id}
    Message ID: {message_id}
    Chat Type: {chat_type}
    Text: {message.text or message.caption or 'No text'}
    """)
    
    # Проверяем, является ли канал одним из привязанных
    channel_ids = db.get_channel_ids()
    logger.info(f"Linked channels: {channel_ids}")
    
    if channel_id not in channel_ids:
        logger.info(f"Ignoring post from non-linked channel: {channel_id}")
        return

    # Получаем контент поста
    content = message.text or message.caption or ""
    if not content:
        logger.info(f"Ignoring post without text content: channel={channel_id}, message={message_id}")
        return

    # Сохраняем пост
    try:
        db.save_post(channel_id, message_id, content)
        logger.info(f"Successfully saved post: channel={channel_id}, message={message_id}")
    except Exception as e:
        logger.error(f"Error saving post: {str(e)}")
        raise

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Запуск бота"""
    # Получаем токен из переменной окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No bot token provided")
        return

    logger.info("Starting bot...")
    
    # Создаем приложение
    application = Application.builder().token(token).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Обработчик для новых постов в каналах
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.TEXT | filters.CAPTION),
        handle_channel_post
    ))
    
    # Обработчик для отредактированных постов
    application.add_handler(MessageHandler(
        filters.UpdateType.EDITED_CHANNEL_POST & (filters.TEXT | filters.CAPTION),
        handle_channel_post
    ))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Bot is ready to start polling")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot stopped")

if __name__ == '__main__':
    main()