from ..models import User, UserCreate
import uuid
from datetime import datetime
from typing import Optional
from .log_service import LogService

class UserService:
    def __init__(self, log_service: LogService):
        self.users = {}  # user_id -> User
        self.tokens = {}  # setup_token -> user_id
        self.telegram_ids = {}  # telegram_id -> user_id
        self.log = log_service

    def create_user(self) -> User:
        user_create = UserCreate()
        user = User(
            id=str(uuid.uuid4()),
            setup_token=user_create.setup_token,
            created_at=user_create.created_at
        )
        self.users[user.id] = user
        self.tokens[user.setup_token] = user.id
        
        self.log.user_connected(user.id, user.setup_token)
        return user

    def get_user_by_token(self, token: str) -> Optional[User]:
        user_id = self.tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        user_id = self.telegram_ids.get(telegram_id)
        if user_id:
            return self.users.get(user_id)
        return None

    def link_telegram(self, setup_token: str, telegram_id: int) -> Optional[User]:
        user_id = self.tokens.get(setup_token)
        if not user_id:
            self.log.error(f"Failed to link Telegram: token {setup_token} not found")
            return None
        
        user = self.users[user_id]
        user.telegram_id = telegram_id
        self.telegram_ids[telegram_id] = user_id
        
        self.log.telegram_linked(user.id, telegram_id, setup_token)
        return user 