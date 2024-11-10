import sqlite3
from contextlib import contextmanager
import time
from typing import Optional, Tuple
import os
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "db/app.db"):
        logger.info(f"Initializing DatabaseService with db_path: {db_path}")
        self.db_path = db_path
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    @contextmanager
    def get_db(self):
        logger.debug("Opening database connection")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            logger.debug("Closing database connection")
            conn.close()

    def init_db(self):
        """Инициализация всех необходимых таблиц"""
        logger.info("Initializing database tables")
        try:
            with self.get_db() as conn:
                # Таблица временных токенов
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS temp_tokens (
                        token TEXT PRIMARY KEY,
                        timestamp FLOAT NOT NULL,
                        admin_id INTEGER NOT NULL
                    )
                """)
                
                # Таблица привязок телеграм аккаунтов
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telegram_bindings (
                        telegram_user_id INTEGER PRIMARY KEY,
                        admin_id INTEGER NOT NULL,
                        created_at FLOAT NOT NULL
                    )
                """)
                
                # Таблица телеграм каналов
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telegram_channels (
                        channel_id INTEGER PRIMARY KEY,
                        admin_id INTEGER NOT NULL,
                        channel_title TEXT NOT NULL,
                        created_at FLOAT NOT NULL
                    )
                """)
                
                # Таблица постов
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id INTEGER NOT NULL,
                        message_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        created_at FLOAT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        FOREIGN KEY (channel_id) REFERENCES telegram_channels (channel_id)
                    )
                """)
                
                # Таблица настроек каналов
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS channel_settings (
                        channel_id INTEGER PRIMARY KEY,
                        auto_posting BOOLEAN NOT NULL DEFAULT 0,
                        post_interval INTEGER DEFAULT 3600,
                        created_at FLOAT NOT NULL,
                        last_updated_at FLOAT NOT NULL,
                        FOREIGN KEY (channel_id) REFERENCES telegram_channels (channel_id)
                    )
                """)

                conn.commit()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def reset_db(self):
        """Пересоздание всех таблиц (удаляет все данные!)"""
        logger.warning("Resetting database - all data will be deleted")
        try:
            with self.get_db() as conn:
                # Удаляем существующие таблицы
                conn.execute("DROP TABLE IF EXISTS posts")
                conn.execute("DROP TABLE IF EXISTS channel_settings")
                conn.execute("DROP TABLE IF EXISTS telegram_channels")
                conn.execute("DROP TABLE IF EXISTS telegram_bindings")
                conn.execute("DROP TABLE IF EXISTS temp_tokens")
                conn.commit()
            
            # Создаем таблицы заново
            self.init_db()
            logger.info("Database reset completed successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {str(e)}")
            raise

    def _validate_admin_id(self, admin_id: int) -> None:
        """Validates that admin_id is positive"""
        if not isinstance(admin_id, int) or admin_id <= 0:
            logger.error(f"Invalid admin_id: {admin_id}")
            raise ValueError(f"Invalid admin_id: {admin_id}. Must be a positive integer.")

    def save_token(self, token: str, admin_id: int) -> None:
        """Сохранение временного токена"""
        self._validate_admin_id(admin_id)
        logger.info(f"Saving temporary token for admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                conn.execute(
                    "INSERT INTO temp_tokens (token, timestamp, admin_id) VALUES (?, ?, ?)",
                    (token, time.time(), admin_id)
                )
                conn.commit()
            logger.debug(f"Token saved successfully for admin_id: {admin_id}")
        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")
            raise

    def get_token_data(self, token: str) -> Optional[Tuple[float, int]]:
        """Получение данных токена"""
        logger.debug(f"Getting token data for token: {token[:8]}...")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT timestamp, admin_id FROM temp_tokens WHERE token = ?",
                    (token,)
                ).fetchone()
                
                if result:
                    logger.debug(f"Token data found for token: {token[:8]}...")
                    return result['timestamp'], result['admin_id']
                logger.debug(f"No token data found for token: {token[:8]}...")
                return None
        except Exception as e:
            logger.error(f"Error getting token data: {str(e)}")
            raise

    def delete_token(self, token: str) -> None:
        """Удаление использованного токена"""
        logger.info(f"Deleting token: {token[:8]}...")
        try:
            with self.get_db() as conn:
                conn.execute("DELETE FROM temp_tokens WHERE token = ?", (token,))
                conn.commit()
            logger.debug(f"Token deleted successfully: {token[:8]}...")
        except Exception as e:
            logger.error(f"Error deleting token: {str(e)}")
            raise

    def save_telegram_binding(self, telegram_user_id: int, admin_id: int) -> None:
        """Сохранение привязки Telegram к админу"""
        self._validate_admin_id(admin_id)
        logger.info(f"Saving Telegram binding for user_id: {telegram_user_id}, admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO telegram_bindings 
                       (telegram_user_id, admin_id, created_at) 
                       VALUES (?, ?, ?)""",
                    (telegram_user_id, admin_id, time.time())
                )
                conn.commit()
            logger.debug(f"Telegram binding saved successfully for user_id: {telegram_user_id}")
        except Exception as e:
            logger.error(f"Error saving Telegram binding: {str(e)}")
            raise

    def get_admin_id_by_telegram(self, telegram_user_id: int) -> Optional[int]:
        """Получение admin_id по telegram_user_id"""
        logger.debug(f"Getting admin_id for telegram_user_id: {telegram_user_id}")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT admin_id FROM telegram_bindings WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                ).fetchone()
                if result:
                    logger.debug(f"Found admin_id: {result[0]} for telegram_user_id: {telegram_user_id}")
                else:
                    logger.debug(f"No admin_id found for telegram_user_id: {telegram_user_id}")
                return result[0] if isinstance(result[0], int) else None
        except Exception as e:
            logger.error(f"Error getting admin_id by telegram: {str(e)}")
            raise

    def cleanup_expired_tokens(self, expiry_seconds: int = 600) -> None:
        """Очистка просроченных токенов"""
        logger.info(f"Cleaning up expired tokens (expiry: {expiry_seconds} seconds)")
        try:
            with self.get_db() as conn:
                conn.execute(
                    "DELETE FROM temp_tokens WHERE timestamp < ?",
                    (time.time() - expiry_seconds,)
                )
                conn.commit()
            logger.debug("Expired tokens cleanup completed")
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            raise

    def get_telegram_user_by_admin(self, admin_id: int) -> Optional[int]:
        """Получение telegram_user_id по admin_id"""
        logger.debug(f"Getting telegram_user_id for admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT telegram_user_id FROM telegram_bindings WHERE admin_id = ?",
                    (admin_id,)
                ).fetchone()
                
                if result:
                    logger.debug(f"Found telegram_user_id: {result[0]} for admin_id: {admin_id}")
                else:
                    logger.debug(f"No telegram_user_id found for admin_id: {admin_id}")
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting telegram user by admin: {str(e)}")
            raise

    def remove_telegram_binding(self, admin_id: int) -> None:
        """Удаление привязки Telegram"""
        logger.info(f"Removing Telegram binding for admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                conn.execute(
                    "DELETE FROM telegram_bindings WHERE admin_id = ?",
                    (admin_id,)
                )
                conn.commit()
            logger.debug(f"Telegram binding removed successfully for admin_id: {admin_id}")
        except Exception as e:
            logger.error(f"Error removing telegram binding: {str(e)}")
            raise

    def save_channel_binding(self, admin_id: int, channel_id: int, channel_title: str) -> None:
        """Сохранение привязки канала"""
        self._validate_admin_id(admin_id)
        logger.info(f"Saving channel binding for admin_id: {admin_id}, channel_id: {channel_id}")
        try:
            with self.get_db() as conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS telegram_channels (
                        channel_id INTEGER PRIMARY KEY,
                        admin_id INTEGER NOT NULL,
                        channel_title TEXT NOT NULL,
                        created_at FLOAT NOT NULL
                    )"""
                )
                conn.execute(
                    """INSERT OR REPLACE INTO telegram_channels 
                       (channel_id, admin_id, channel_title, created_at) 
                       VALUES (?, ?, ?, ?)""",
                    (channel_id, admin_id, channel_title, time.time())
                )
                conn.commit()
            logger.debug(f"Channel binding saved successfully for channel_id: {channel_id}")
        except Exception as e:
            logger.error(f"Error saving channel binding: {str(e)}")
            raise

    def get_channel_by_id(self, channel_id: int) -> Optional[dict]:
        """Получение информации о канале по его ID"""
        logger.debug(f"Getting channel info for channel_id: {channel_id}")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    """SELECT channel_id, admin_id, channel_title, created_at 
                       FROM telegram_channels 
                       WHERE channel_id = ?""",
                    (channel_id,)
                ).fetchone()
                
                if result:
                    channel_info = dict(result)
                    logger.debug(f"Found channel info: {channel_info}")
                    return channel_info
                logger.debug(f"No channel found for channel_id: {channel_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting channel by id: {str(e)}")
            raise

    def is_channel_linked(self, channel_id: int) -> bool:
        """Проверка, привязан ли канал"""
        logger.debug(f"Checking if channel {channel_id} is linked")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT 1 FROM telegram_channels WHERE channel_id = ?",
                    (channel_id,)
                ).fetchone()
                is_linked = bool(result)
                logger.debug(f"Channel {channel_id} linked status: {is_linked}")
                return is_linked
        except Exception as e:
            logger.error(f"Error checking channel link status: {str(e)}")
            raise

    def has_linked_channel(self, telegram_user_id: int) -> bool:
        """Проверка наличия привязанного канала у telegram пользователя"""
        logger.debug(f"Checking if telegram_user_id {telegram_user_id} has linked channel")
        try:
            with self.get_db() as conn:
                # Сначала получаем admin_id по telegram_user_id
                admin_result = conn.execute(
                    "SELECT admin_id FROM telegram_bindings WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                ).fetchone()
                
                if not admin_result:
                    logger.debug(f"No admin_id found for telegram_user_id: {telegram_user_id}")
                    return False
                
                admin_id = admin_result[0]
                
                # Теперь проверяем наличие канала для этого admin_id
                channel_result = conn.execute(
                    "SELECT 1 FROM telegram_channels WHERE admin_id = ?",
                    (admin_id,)
                ).fetchone()
                
                has_channel = bool(channel_result)
                logger.debug(f"Telegram user {telegram_user_id} has linked channel: {has_channel}")
                return has_channel
        except Exception as e:
            logger.error(f"Error checking linked channel status: {str(e)}")
            raise

    def get_user_channels(self, telegram_user_id: int) -> list:
        """��учеие списка всех каналов пользователя"""
        logger.debug(f"Getting channels for telegram_user_id {telegram_user_id}")
        try:
            with self.get_db() as conn:
                # Получаем admin_id
                admin_result = conn.execute(
                    "SELECT admin_id FROM telegram_bindings WHERE telegram_user_id = ?",
                    (telegram_user_id,)
                ).fetchone()
                
                if not admin_result:
                    logger.debug(f"No admin_id found for telegram_user_id: {telegram_user_id}")
                    return []
                
                admin_id = admin_result[0]
                
                # Получаем все каналы пользователя
                channels = conn.execute(
                    """SELECT channel_id, channel_title, created_at 
                       FROM telegram_channels 
                       WHERE admin_id = ?""",
                    (admin_id,)
                ).fetchall()
                
                result = [dict(channel) for channel in channels]
                logger.debug(f"Found {len(result)} channels for telegram_user_id {telegram_user_id}")
                return result
        except Exception as e:
            logger.error(f"Error getting user channels: {str(e)}")
            raise

    def has_channel_by_admin_id(self, admin_id: int) -> bool:
        """Проверка наличия канала у админа по admin_id"""
        logger.debug(f"Checking if admin_id {admin_id} has any channels")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT channel_id FROM telegram_channels WHERE admin_id = ? LIMIT 1",
                    (admin_id,)
                ).fetchone()
                
                has_channel = bool(result)
                if has_channel:
                    channel_id = result[0]
                    logger.info(f"Found channel {channel_id} for admin_id {admin_id}")
                else:
                    logger.info(f"No channels found for admin_id {admin_id}")
                return has_channel
        except Exception as e:
            logger.error(f"Error checking channel existence for admin_id: {str(e)}")
            raise

    def remove_all_telegram_bindings(self, admin_id: int) -> None:
        """Удаление всех привязок Telegram (аккаунт и каналы)"""
        logger.info(f"Removing all Telegram bindings for admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                # Удаляем привязку аккаунта
                conn.execute(
                    "DELETE FROM telegram_bindings WHERE admin_id = ?",
                    (admin_id,)
                )
                # Удаляем привязки каналов
                conn.execute(
                    "DELETE FROM telegram_channels WHERE admin_id = ?",
                    (admin_id,)
                )
                conn.commit()
            logger.info(f"All Telegram bindings removed for admin_id: {admin_id}")
        except Exception as e:
            logger.error(f"Error removing all telegram bindings: {str(e)}")
            raise

    def remove_channel_binding(self, admin_id: int) -> None:
        """Удаление привязки канала"""
        logger.info(f"Removing channel binding for admin_id: {admin_id}")
        try:
            with self.get_db() as conn:
                conn.execute(
                    "DELETE FROM telegram_channels WHERE admin_id = ?",
                    (admin_id,)
                )
                conn.commit()
            logger.info(f"Channel binding removed for admin_id: {admin_id}")
        except Exception as e:
            logger.error(f"Error removing channel binding: {str(e)}")
            raise

    def save_post(self, channel_id: int, message_id: int, content: str) -> None:
        """Сохранение нового поста из канала"""
        logger.info(f"Saving new post from channel {channel_id}, message_id: {message_id}")
        try:
            with self.get_db() as conn:
                # Проверяем, существует ли уже такой пост
                existing = conn.execute(
                    """SELECT 1 FROM posts 
                       WHERE channel_id = ? AND message_id = ?""",
                    (channel_id, message_id)
                ).fetchone()
                
                if not existing:
                    conn.execute(
                        """INSERT INTO posts 
                           (channel_id, message_id, content, created_at, status) 
                           VALUES (?, ?, ?, ?, ?)""",
                        (channel_id, message_id, content, time.time(), 'pending')
                    )
                    conn.commit()
                    logger.info(f"New post saved: channel_id={channel_id}, message_id={message_id}")
                else:
                    logger.debug(f"Post already exists: channel_id={channel_id}, message_id={message_id}")
        except Exception as e:
            logger.error(f"Error saving post: {str(e)}")
            raise

    def get_channel_ids(self) -> list[int]:
        """Получение списка всех привязанных channel_id"""
        logger.debug("Getting all channel IDs")
        try:
            with self.get_db() as conn:
                result = conn.execute(
                    "SELECT channel_id FROM telegram_channels"
                ).fetchall()
                channel_ids = [row[0] for row in result]
                logger.debug(f"Found {len(channel_ids)} channels: {channel_ids}")
                return channel_ids
        except Exception as e:
            logger.error(f"Error getting channel IDs: {str(e)}")
            raise