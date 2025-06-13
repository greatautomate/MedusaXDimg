"""Database operations for MedusaXD Bot using MongoDB"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, mongodb_url: str):
        self.mongodb_url = mongodb_url
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client.medusaxd_bot

            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("user_id", unique=True)
            await self.db.users.create_index("username")

            # Admins collection indexes
            await self.db.admins.create_index("user_id", unique=True)

            # Bans collection indexes
            await self.db.bans.create_index("user_id", unique=True)

            # Logs collection indexes
            await self.db.logs.create_index("timestamp")
            await self.db.logs.create_index("user_id")
            await self.db.logs.create_index("action_type")

            # Rate limiting collection indexes
            await self.db.rate_limits.create_index("user_id")
            await self.db.rate_limits.create_index("timestamp")

            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")

    # User Management
    async def add_authorized_user(self, user_id: int, username: str = None, added_by: int = None) -> bool:
        """Add a user to authorized users"""
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "authorized_at": datetime.utcnow(),
                "added_by": added_by,
                "total_generations": 0,
                "last_active": datetime.utcnow()
            }

            await self.db.users.update_one(
                {"user_id": user_id},
                {"$setOnInsert": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add authorized user {user_id}: {e}")
            return False

    async def remove_authorized_user(self, user_id: int) -> bool:
        """Remove a user from authorized users"""
        try:
            result = await self.db.users.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to remove authorized user {user_id}: {e}")
            return False

    async def is_user_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            return user is not None
        except Exception as e:
            logger.error(f"Failed to check user authorization {user_id}: {e}")
            return False

    async def get_authorized_users(self) -> List[Dict]:
        """Get all authorized users"""
        try:
            cursor = self.db.users.find({})
            users = await cursor.to_list(length=None)
            return users
        except Exception as e:
            logger.error(f"Failed to get authorized users: {e}")
            return []

    async def update_user_activity(self, user_id: int, username: str = None):
        """Update user's last activity"""
        try:
            update_data = {"last_active": datetime.utcnow()}
            if username:
                update_data["username"] = username

            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"Failed to update user activity {user_id}: {e}")

    async def increment_user_generations(self, user_id: int):
        """Increment user's generation count"""
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_generations": 1}}
            )
        except Exception as e:
            logger.error(f"Failed to increment generations for user {user_id}: {e}")

    # Admin Management
    async def add_admin(self, user_id: int) -> bool:
        """Add admin user"""
        try:
            admin_data = {
                "user_id": user_id,
                "added_at": datetime.utcnow()
            }

            await self.db.admins.update_one(
                {"user_id": user_id},
                {"$setOnInsert": admin_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add admin {user_id}: {e}")
            return False

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        try:
            admin = await self.db.admins.find_one({"user_id": user_id})
            return admin is not None
        except Exception as e:
            logger.error(f"Failed to check admin status {user_id}: {e}")
            return False

    # Ban System
    async def ban_user(self, user_id: int, reason: str = "No reason provided", banned_by: int = None) -> bool:
        """Ban a user"""
        try:
            ban_data = {
                "user_id": user_id,
                "reason": reason,
                "banned_at": datetime.utcnow(),
                "banned_by": banned_by
            }

            await self.db.bans.update_one(
                {"user_id": user_id},
                {"$set": ban_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to ban user {user_id}: {e}")
            return False

    async def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        try:
            result = await self.db.bans.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to unban user {user_id}: {e}")
            return False

    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        try:
            ban = await self.db.bans.find_one({"user_id": user_id})
            return ban is not None
        except Exception as e:
            logger.error(f"Failed to check ban status {user_id}: {e}")
            return False

    async def get_ban_info(self, user_id: int) -> Dict:
        """Get ban information for user"""
        try:
            ban = await self.db.bans.find_one({"user_id": user_id})
            return ban or {}
        except Exception as e:
            logger.error(f"Failed to get ban info {user_id}: {e}")
            return {}

    async def get_banned_users(self) -> List[Dict]:
        """Get all banned users"""
        try:
            cursor = self.db.bans.find({})
            bans = await cursor.to_list(length=None)
            return bans
        except Exception as e:
            logger.error(f"Failed to get banned users: {e}")
            return []

    # Bot Status
    async def set_bot_status(self, enabled: bool) -> bool:
        """Set bot enabled/disabled status"""
        try:
            await self.db.bot_settings.update_one(
                {"setting": "bot_status"},
                {"$set": {"enabled": enabled, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set bot status: {e}")
            return False

    async def get_bot_status(self) -> Dict:
        """Get bot status"""
        try:
            status = await self.db.bot_settings.find_one({"setting": "bot_status"})
            return status or {"enabled": True}
        except Exception as e:
            logger.error(f"Failed to get bot status: {e}")
            return {"enabled": True}

    # Rate Limiting
    async def check_rate_limit(self, user_id: int, limit_minutes: int = 5, max_requests: int = 10) -> bool:
        """Check if user has exceeded rate limit"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=limit_minutes)

            # Count recent requests
            count = await self.db.rate_limits.count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": cutoff_time}
            })

            return count < max_requests
        except Exception as e:
            logger.error(f"Failed to check rate limit for user {user_id}: {e}")
            return True  # Allow on error

    async def record_request(self, user_id: int):
        """Record a user request for rate limiting"""
        try:
            await self.db.rate_limits.insert_one({
                "user_id": user_id,
                "timestamp": datetime.utcnow()
            })

            # Clean old records (older than 1 hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            await self.db.rate_limits.delete_many({
                "timestamp": {"$lt": cutoff_time}
            })
        except Exception as e:
            logger.error(f"Failed to record request for user {user_id}: {e}")

    # Logging
    async def log_generation(self, user_id: int, username: str, prompt: str, model: str, 
                           images: List[str], success: bool = True, error: str = None):
        """Log image generation"""
        try:
            log_data = {
                "user_id": user_id,
                "username": username,
                "action_type": "IMAGE_GENERATION",
                "prompt": prompt,
                "model": model,
                "images": images,
                "success": success,
                "error": error,
                "timestamp": datetime.utcnow()
            }

            await self.db.logs.insert_one(log_data)
        except Exception as e:
            logger.error(f"Failed to log generation: {e}")

    async def log_admin_action(self, admin_id: int, action: str, target_user: int = None, details: str = None):
        """Log admin actions"""
        try:
            log_data = {
                "admin_id": admin_id,
                "action_type": "ADMIN_ACTION",
                "action": action,
                "target_user": target_user,
                "details": details,
                "timestamp": datetime.utcnow()
            }

            await self.db.logs.insert_one(log_data)
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")

    # Statistics
    async def get_stats(self) -> Dict:
        """Get bot statistics"""
        try:
            total_users = await self.db.users.count_documents({})
            total_banned = await self.db.bans.count_documents({})
            total_generations = await self.db.logs.count_documents({"action_type": "IMAGE_GENERATION", "success": True})

            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(days=1)
            recent_generations = await self.db.logs.count_documents({
                "action_type": "IMAGE_GENERATION",
                "success": True,
                "timestamp": {"$gte": recent_cutoff}
            })

            # Active users (last 7 days)
            active_cutoff = datetime.utcnow() - timedelta(days=7)
            active_users = await self.db.users.count_documents({
                "last_active": {"$gte": active_cutoff}
            })

            return {
                "total_users": total_users,
                "total_banned": total_banned,
                "total_generations": total_generations,
                "recent_generations_24h": recent_generations,
                "active_users_7d": active_users
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
