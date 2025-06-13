"""Logging system for MedusaXD Bot"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class BotLogger:
    def __init__(self, bot_token: str, log_channel_id: str):
        self.bot = Bot(token=bot_token)
        self.log_channel_id = log_channel_id

    async def log_image_generation(self, user_id: int, username: str, prompt: str, 
                                 model: str, aspect_ratio: str, image_urls: List[str]):
        """Log image generation to admin channel"""
        try:
            log_message = (
                f"🎨 **IMAGE GENERATED**\n\n"
                f"**👤 User:** @{username} (`{user_id}`)\n"
                f"**🤖 Model:** `{model}`\n"
                f"**📐 Aspect:** `{aspect_ratio}`\n"
                f"**🖼️ Images:** {len(image_urls)}\n"
                f"**⏰ Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
                f"**📝 Prompt:**\n`{prompt}`\n\n"
                f"**🔗 Image URLs:**"
            )

            # Send the log message
            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode='Markdown'
            )

            # Send image URLs as separate messages to avoid message length limits
            for i, url in enumerate(image_urls, 1):
                await self.bot.send_message(
                    chat_id=self.log_channel_id,
                    text=f"🖼️ **Image {i}:** {url}"
                )

        except TelegramError as e:
            logger.error(f"Failed to log image generation to channel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging image generation: {e}")

    async def log_user_action(self, user_id: int, username: str, action: str, action_type: str):
        """Log user actions to admin channel"""
        try:
            log_message = (
                f"👤 **USER ACTION**\n\n"
                f"**User:** @{username} (`{user_id}`)\n"
                f"**Action:** `{action}`\n"
                f"**Type:** {action_type}\n"
                f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode='Markdown'
            )

        except TelegramError as e:
            logger.error(f"Failed to log user action to channel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging user action: {e}")

    async def log_admin_action(self, admin_id: int, action: str, target_user: Optional[int] = None):
        """Log admin actions to admin channel"""
        try:
            log_message = (
                f"🔧 **ADMIN ACTION**\n\n"
                f"**Admin:** `{admin_id}`\n"
                f"**Action:** {action}\n"
            )

            if target_user:
                log_message += f"**Target User:** `{target_user}`\n"

            log_message += f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode='Markdown'
            )

        except TelegramError as e:
            logger.error(f"Failed to log admin action to channel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging admin action: {e}")

    async def log_system_event(self, event: str, event_type: str):
        """Log system events to admin channel"""
        try:
            log_message = (
                f"🤖 **SYSTEM EVENT**\n\n"
                f"**Event:** {event}\n"
                f"**Type:** {event_type}\n"
                f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode='Markdown'
            )

        except TelegramError as e:
            logger.error(f"Failed to log system event to channel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging system event: {e}")

    async def log_error(self, error: str, user_id: Optional[int] = None, context: Optional[str] = None):
        """Log errors to admin channel"""
        try:
            log_message = (
                f"❌ **ERROR**\n\n"
                f"**Error:** {error}\n"
            )

            if user_id:
                log_message += f"**User:** `{user_id}`\n"

            if context:
                log_message += f"**Context:** {context}\n"

            log_message += f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

            await self.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode='Markdown'
            )

        except TelegramError as e:
            logger.error(f"Failed to log error to channel: {e}")
        except Exception as e:
            logger.error(f"Unexpected error logging error: {e}")
