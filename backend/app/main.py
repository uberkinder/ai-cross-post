from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import time
import secrets
from .services.db_service import DatabaseService
import logging
import os

# Create log directory if it doesn't exist
os.makedirs('logs/backend', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/server.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('backend')

app = FastAPI(title="AI Cross-Post API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Инициализация сервиса базы данных
db = DatabaseService()

class TelegramVerification(BaseModel):
    token: str
    telegram_user_id: int

class ChannelLink(BaseModel):
    telegram_user_id: int
    channel_id: int
    channel_title: str

    class Config:
        extra = "ignore"  # Игнорировать дополнительные поля

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/telegram/setup")
async def setup_telegram():
    """Генерирует токен и возвращает URL для настройки бота, или возвращает существующее подключение"""
    logger.info("Checking existing connection...")
    
    # Сначала проверяем существующую привязку
    admin_id = 666  # В будущем здесь будет реальный admin_id
    telegram_user = db.get_telegram_user_by_admin(admin_id)
    
    if telegram_user:
        logger.info(f"Found existing connection for admin_id {admin_id}")
        return {
            "connected": True,
            "telegram_user_id": telegram_user
        }
    
    # Если привязки нет, генерируем новый токен
    logger.info("No existing connection, generating new token...")
    token = secrets.token_urlsafe(16)
    logger.info(f"Generated token: {token}")
    
    # Сохраняем токен с временем создания и admin_id
    db.save_token(token, admin_id=666)
    bot_url = f"https://t.me/feedsAIbot?start={token}"
    
    response_data = {
        "connected": False,
        "token": token,
        "bot_url": bot_url
    }
    logger.info(f"Returning response: {response_data}")
    return response_data

@app.post("/api/telegram/verify")
async def verify_telegram(data: TelegramVerification):
    """Проверяет токен и привязывает Telegram аккаунт"""
    # Очищаем просроченные токены
    db.cleanup_expired_tokens()
    
    # Получаем данные токена
    token_data = db.get_token_data(data.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid token")
        
    timestamp, admin_id = token_data
    
    # Проверяем не истек ли токен (10 минут)
    if time.time() - timestamp > 600:
        db.delete_token(data.token)
        raise HTTPException(status_code=400, detail="Token expired")
    
    # Привязываем telegram_user_id к admin_id
    db.save_telegram_binding(data.telegram_user_id, admin_id)
    
    # Удаляем использованный токен
    db.delete_token(data.token)
    
    return {"status": "success"} 

@app.middleware("http")
async def log_requests(request, call_next):
    # Log request
    request_body = await request.body()
    logger.info(f"""
=== Incoming Request ===
Method: {request.method}
URL: {request.url}
Headers: {dict(request.headers)}
Origin: {request.headers.get('origin')}
Body: {request_body.decode() if request_body else 'No body'}
======================""")

    response = await call_next(request)
    
    # Log response
    logger.info(f"""
=== Outgoing Response ===
Status: {response.status_code}
Headers: {dict(response.headers)}
======================""")
    return response

@app.get("/api/telegram/check-connection")
async def check_telegram_connection(authorization: str = Header(None)):
    """Проверяет статус подключения Telegram"""
    logger.info("Checking Telegram connection...")
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.split(' ')[1]
    logger.info(f"Checking connection for token: {token}")
    
    # Сначала проверяем временный токен
    token_data = db.get_token_data(token)
    if token_data:
        timestamp, admin_id = token_data
        if time.time() - timestamp > 600:
            db.delete_token(token)
            return {"connected": False}
        return {"connected": True}
    
    # Если временного токена нет, проверяем постоянную привязку
    admin_id = 666  # В будущем здесь будет реальный admin_id
    telegram_user = db.get_telegram_user_by_admin(admin_id)
    if telegram_user:
        return {"connected": True, "telegram_user_id": telegram_user}
    
    return {"connected": False}

@app.post("/api/telegram/disconnect")
async def disconnect_telegram(authorization: str = Header(None)):
    """Отвязывает Telegram аккаунт"""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    admin_id = 666  # В будущем здесь будет реальный admin_id
    db.remove_telegram_binding(admin_id)
    return {"status": "success"}

@app.get("/api/telegram/check-permissions")
async def check_telegram_permissions(authorization: str = Header(None)):
    """Проверяет права бота в канале"""
    logger.info("Checking Telegram permissions...")
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.split(' ')[1]
    logger.info(f"Checking permissions for token: {token}")
    
    # Здесь будет реальная проверка прав бота в канале
    # Пока возвращам заглушку
    return {"hasPermissions": True}

@app.post("/api/telegram/link-channel")
async def link_channel(data: ChannelLink):
    """Привязывает Telegram канал к пользователю"""
    logger.info(f"Linking channel {data.channel_title} for user {data.telegram_user_id}")
    
    # Получаем admin_id по telegram_user_id
    logger.info(f"Getting admin_id for telegram_user_id: {data.telegram_user_id}")
    admin_id = db.get_admin_id_by_telegram(data.telegram_user_id)
    if not admin_id:
        logger.error(f"Admin_id not found for telegram_user_id: {data.telegram_user_id}")
        raise HTTPException(status_code=400, detail="User not found")
    
    # Сохраняем привязку канала
    logger.info(f"Saving channel binding for admin_id: {admin_id}")
    db.save_channel_binding(
        admin_id=admin_id,
        channel_id=data.channel_id,
        channel_title=data.channel_title
    )
    
    return {"status": "success"}

@app.get("/api/telegram/check-channel")
async def check_telegram_channel(authorization: str = Header(None)):
    """Проверяет привязан ли канал к пользователю"""
    logger.info("Checking if channel is linked...")
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    admin_id = 666  # В будущем здесь будет реальный admin_id
    
    # Проверяем наличие канала у админа
    has_channel = db.has_channel_by_admin_id(admin_id)
    logger.info(f"Channel check result for admin_id {admin_id}: {has_channel}")
    
    return {"hasChannel": has_channel}

@app.post("/api/telegram/disconnect-all")
async def disconnect_all_telegram(authorization: str = Header(None)):
    """Отвязывает Telegram аккаунт и все каналы"""
    logger.info("Disconnecting all Telegram bindings...")
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    admin_id = 666  # В будущем здесь будет реальный admin_id
    db.remove_all_telegram_bindings(admin_id)
    
    return {"status": "success"}

@app.post("/api/telegram/disconnect-channel")
async def disconnect_channel(authorization: str = Header(None)):
    """Отвязывает только Telegram канал"""
    logger.info("Disconnecting Telegram channel...")
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    admin_id = 666  # В будущем здесь будет реальный admin_id
    db.remove_channel_binding(admin_id)
    
    return {"status": "success"}