from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
import asyncio
from ..models import Post
from .ai_service import AIService
import os
from dotenv import load_dotenv
from datetime import datetime
import random
import string
import logging
from aiogram import Router
from .log_service import LogService
from .user_service import UserService
from .database_service import DatabaseService

load_dotenv()

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class TelegramService:
    def __init__(self, ai_service: AIService, user_service: UserService, log_service: LogService):
        self.bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        self.dp = Dispatcher()
        self.blog_router = Router()
        self.user_service = user_service
        self.log = log_service
        self.db = DatabaseService()
        self.posts_queue = []
        self.user_channels = {}
        self.verification_requests = {}
        self.setup_handlers()

    def setup_handlers(self):
        @self.dp.message(Command("start"))
        async def start_handler(message: types.Message, command: CommandObject):
            setup_token = command.args

            if setup_token:
                # Пытаемся связать Telegram аккаунт с пользователем по токену
                user = self.user_service.link_telegram(setup_token, message.from_user.id)
                if user:
                    self.log.telegram_linked(user.id, message.from_user.id, setup_token)
                    await message.answer(
                        "✅ Successfully connected!\n\n"
                        "Now you can:\n"
                        "1. Add me to your channel as an admin\n"
                        "2. Forward any message from your channel to verify ownership"
                    )
                else:
                    await message.answer("❌ Invalid or expired setup token. Please try again with a valid token.")
            else:
                await message.answer(
                    "Welcome to AI Cross-Post!\n"
                    "Please use the setup link from the web interface to connect your account."
                )

        @self.dp.message(Command("getid"))
        async def get_id_handler(message: types.Message):
            await message.answer(f"Chat ID: {message.chat.id}")

        @self.dp.message(F.forward_from_chat)
        async def handle_forwarded(message: types.Message):
            user = self.user_service.get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("❌ Please connect your account first using the setup link from the web interface.")
                return

            channel_id = message.forward_from_chat.id
            channel_title = message.forward_from_chat.title

            # Проверяем права бота в канале
            try:
                bot_member = await self.bot.get_chat_member(channel_id, self.bot.id)
                if not bot_member.is_admin():
                    await message.answer(
                        "❌ I need to be an admin in the channel first!\n"
                        "Please add me as an admin with these permissions:\n"
                        "- Read Messages\n"
                        "- Send Messages\n"
                        "- Edit Messages\n"
                        "- Delete Messages"
                    )
                    return

                # Проверяем права пользователя в канале
                user_member = await self.bot.get_chat_member(channel_id, message.from_user.id)
                if not user_member.is_admin():
                    await message.answer("❌ You need to be an admin in the channel to connect it.")
                    return

                # Всё ок, сохраняем канал
                if user.id not in self.user_channels:
                    self.user_channels[user.id] = {}
                
                self.user_channels[user.id][channel_id] = True
                self.log.channel_verified(user.id, channel_id, channel_title)

                await message.answer(
                    "✅ Channel successfully connected!\n\n"
                    f"Channel: {channel_title}\n"
                    f"ID: {channel_id}\n\n"
                    "I'll start monitoring posts in this channel."
                )

            except Exception as e:
                self.log.error(f"Error verifying channel: {e}", user_id=user.id)
                await message.answer("❌ Error verifying channel. Please try again.")

        @self.dp.channel_post()
        async def handle_any_channel_content(message: types.Message):
            """Отлавливаем все типы контента из каналов"""
            logger.info(f"Received any channel content. Chat ID: {message.chat.id}, "
                         f"Message ID: {message.message_id}, "
                         f"Content Type: {message.content_type}")

        @self.dp.edited_channel_post()
        async def handle_edited_channel_post(message: types.Message):
            logger.info(f"Received edited channel post: {message}")

    async def get_posts(self):
        """Получить все посты из очереди"""
        return self.posts_queue

    async def remove_post(self, post_id: int):
        """Удалить пост из очереди"""
        self.posts_queue = [p for p in self.posts_queue if p['id'] != post_id]

    async def start(self):
        """Start the bot polling"""
        try:
            logger.info("Starting Telegram bot...")
            await self.dp.start_polling(self.bot, allowed_updates=[
                "message",
                "edited_message",
                "channel_post",
                "edited_channel_post"
            ])
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")

    async def stop(self):
        """Stop the bot"""
        await self.bot.session.close()

    async def send_message(self, chat_id: str, message: str):
        """Send a message to a specific chat"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def verify_channel_ownership(self, user_id: int, channel_id: int) -> bool:
        # 1. Проверяем, является ли бот админом канала
        chat_member = await self.bot.get_chat_member(channel_id, self.bot.id)
        if not chat_member.is_admin():
            return False

        # 2. Генерируем уникальный код верификации
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # 3. Сохраняем запрос на верификацию
        self.verification_requests[channel_id] = {
            'user_id': user_id,
            'code': verification_code,
            'timestamp': datetime.now()
        }

        # 4. Просим пользователя отправить код через канал
        await self.bot.send_message(
            user_id,
            f"To verify channel ownership, please post this code in your channel:\n"
            f"`{verification_code}`\n"
            f"The code will expire in 10 minutes."
        )

        return True