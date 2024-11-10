from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class User(BaseModel):
    id: str
    telegram_id: Optional[int] = None
    setup_token: str
    created_at: datetime

class UserCreate(BaseModel):
    setup_token: str = str(uuid.uuid4())
    created_at: datetime = datetime.now()

class Post(BaseModel):
    content: str
    platform: str
    scheduled_time: Optional[datetime] = None

class CrossPostRequest(BaseModel):
    source_platform: str
    target_platform: str
    content: str

class CrossPostResponse(BaseModel):
    status: str
    message: str
    transformed_content: Optional[str] = None

class TelegramChannel(BaseModel):
    id: int
    title: str
    user_id: str
    verified: bool = False