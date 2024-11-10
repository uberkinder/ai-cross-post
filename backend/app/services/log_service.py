import logging
from datetime import datetime
import os
from typing import Optional

class LogService:
    def __init__(self):
        # Создаем директорию для логов если её нет
        os.makedirs('logs', exist_ok=True)
        
        # Настраиваем основной логгер
        self.logger = logging.getLogger('ai_cross_post')
        self.logger.setLevel(logging.INFO)
        
        # Форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Хендлер для файла
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def user_connected(self, user_id: str, setup_token: str):
        self.logger.info(f"New user created | ID: {user_id} | Token: {setup_token}")

    def telegram_linked(self, user_id: str, telegram_id: int, setup_token: str):
        self.logger.info(
            f"Telegram account linked | User ID: {user_id} | "
            f"Telegram ID: {telegram_id} | Token: {setup_token}"
        )

    def channel_verified(self, user_id: str, channel_id: int, channel_title: str):
        self.logger.info(
            f"Channel verified | User ID: {user_id} | "
            f"Channel ID: {channel_id} | Channel: {channel_title}"
        )

    def post_received(self, user_id: str, channel_id: int, post_id: int):
        self.logger.info(
            f"New post received | User ID: {user_id} | "
            f"Channel ID: {channel_id} | Post ID: {post_id}"
        )

    def post_transformed(
        self, 
        user_id: str, 
        from_platform: str, 
        to_platform: str,
        original_content: str,
        transformed_content: str
    ):
        self.logger.info(
            f"Content transformed | User ID: {user_id} | "
            f"From: {from_platform} | To: {to_platform}"
        )
        self.logger.debug(f"Original content: {original_content}")
        self.logger.debug(f"Transformed content: {transformed_content}")

    def error(self, message: str, user_id: Optional[str] = None, error: Optional[Exception] = None):
        if user_id:
            self.logger.error(f"Error for user {user_id} | {message}", exc_info=error)
        else:
            self.logger.error(message, exc_info=error) 