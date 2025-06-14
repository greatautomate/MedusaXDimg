"""
Enhanced Logging System for MedusaXD Bot
Comprehensive logging with Hydrogram integration and advanced features
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from hydrogram import Client
from hydrogram.errors import FloodWait, ChatWriteForbidden, ChannelInvalid, UserDeactivated
import time
import traceback

logger = logging.getLogger(__name__)

class BotLogger:
    def __init__(self, bot_token: str, log_channel_id: str):
        self.bot_token = bot_token
        self.log_channel_id = int(log_channel_id) if log_channel_id.lstrip('-').isdigit() else log_channel_id

        # Create a separate client for logging
        self.log_client = None
        self.is_initialized = False
        self.failed_messages = []  # Store failed messages for retry

        # Statistics tracking
        self.stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_error": None,
            "start_time": datetime.utcnow()
        }

    async def initialize(self, api_id: int, api_hash: str):
        """Initialize the logging client with comprehensive error handling"""
        try:
            self.log_client = Client(
                "medusaxd_logger",
                bot_token=self.bot_token,
                api_id=api_id,
                api_hash=api_hash
            )

            await self.log_client.start()
            self.is_initialized = True
            logger.info("✅ Logger client initialized successfully")

            # Test the log channel
            await self._test_log_channel()

            # Start background task for retry failed messages
            asyncio.create_task(self._retry_failed_messages())

        except Exception as e:
            logger.error(f"❌ Failed to initialize logger client: {e}")
            self.stats["last_error"] = str(e)

    async def _test_log_channel(self):
        """Test if we can send messages to the log channel"""
        try:
            test_message = (
                "🤖 **MedusaXD Logger Initialized**\n\n"
                f"✅ Logger successfully connected\n"
                f"📅 Start Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"🆔 Channel ID: `{self.log_channel_id}`\n"
                f"🎯 Target: Image generation logging\n\n"
                "**Features Active:**\n"
                "• Image generation logs\n"
                "• User action tracking\n"
                "• Admin action logging\n"
                "• System event monitoring\n"
                "• Error reporting\n"
                "• Statistics tracking\n\n"
                "🚀 **Ready to log all bot activities!**"
            )

            await self.log_client.send_message(
                chat_id=self.log_channel_id,
                text=test_message
            )
            logger.info("✅ Log channel test successful")
            self.stats["messages_sent"] += 1

        except ChannelInvalid:
            error_msg = "❌ Invalid log channel ID - bot might not be added to the channel"
            logger.error(error_msg)
            self.stats["last_error"] = error_msg
        except ChatWriteForbidden:
            error_msg = "❌ Bot doesn't have permission to write in the log channel"
            logger.error(error_msg)
            self.stats["last_error"] = error_msg
        except Exception as e:
            error_msg = f"❌ Log channel test failed: {e}"
            logger.error(error_msg)
            self.stats["last_error"] = error_msg

    async def _send_log_message(self, message: str, retry_count: int = 3, priority: str = "normal") -> bool:
        """Send message to log channel with comprehensive error handling"""
        if not self.log_client or not self.is_initialized:
            logger.error("❌ Logger client not initialized")
            self._store_failed_message(message, priority)
            return False

        for attempt in range(retry_count):
            try:
                await self.log_client.send_message(
                    chat_id=self.log_channel_id,
                    text=message,
                    disable_web_page_preview=True
                )
                self.stats["messages_sent"] += 1
                return True

            except FloodWait as e:
                logger.warning(f"⏳ Flood wait: {e.value}s (attempt {attempt + 1})")
                await asyncio.sleep(e.value)
                continue

            except ChannelInvalid:
                error_msg = "❌ Invalid log channel - check channel ID and bot permissions"
                logger.error(error_msg)
                self.stats["last_error"] = error_msg
                self.stats["messages_failed"] += 1
                return False

            except ChatWriteForbidden:
                error_msg = "❌ Bot forbidden from writing to log channel"
                logger.error(error_msg)
                self.stats["last_error"] = error_msg
                self.stats["messages_failed"] += 1
                return False

            except UserDeactivated:
                error_msg = "❌ Bot account deactivated"
                logger.error(error_msg)
                self.stats["last_error"] = error_msg
                self.stats["messages_failed"] += 1
                return False

            except Exception as e:
                logger.error(f"❌ Failed to send log message (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.stats["messages_failed"] += 1
                    self.stats["last_error"] = str(e)
                    self._store_failed_message(message, priority)
                continue

        return False

    def _store_failed_message(self, message: str, priority: str = "normal"):
        """Store failed messages for later retry"""
        self.failed_messages.append({
            "message": message,
            "priority": priority,
            "timestamp": datetime.utcnow(),
            "retry_count": 0
        })

        # Limit stored messages to prevent memory issues
        if len(self.failed_messages) > 100:
            self.failed_messages = self.failed_messages[-50:]  # Keep last 50

    async def _retry_failed_messages(self):
        """Background task to retry failed messages"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                if not self.failed_messages:
                    continue

                # Retry messages with exponential backoff
                for msg_data in self.failed_messages[:]:
                    if msg_data["retry_count"] < 3:
                        success = await self._send_log_message(
                            msg_data["message"], 
                            retry_count=1
                        )

                        if success:
                            self.failed_messages.remove(msg_data)
                            logger.info("✅ Successfully retried failed log message")
                        else:
                            msg_data["retry_count"] += 1
                    else:
                        # Remove messages that failed too many times
                        self.failed_messages.remove(msg_data)
                        logger.warning("⚠️ Dropped log message after max retries")

            except Exception as e:
                logger.error(f"Error in retry task: {e}")
                await asyncio.sleep(300)  # Wait longer on error

    async def log_image_generation(self, user_id: int, username: str, prompt: str, 
                                 model: str, aspect_ratio: str, image_urls: List[str], 
                                 generation_time: float = 0, seed: Optional[int] = None,
                                 style: str = "realistic", num_images: int = 1):
        """Log image generation with comprehensive details"""
        try:
            # Escape special characters for Telegram
            safe_username = self._escape_markdown(username)
            safe_prompt = self._escape_markdown(prompt)

            # Create detailed log message
            log_message = (
                f"🎨 **IMAGE GENERATION**\n\n"
                f"**👤 User:** @{safe_username} (`{user_id}`)\n"
                f"**🤖 Model:** `{model.upper()}`\n"
                f"**📐 Aspect:** `{aspect_ratio.title()}` ({self._get_ratio_size(aspect_ratio)})\n"
                f"**🎨 Style:** `{style.title()}`\n"
                f"**🖼️ Images:** {len(image_urls)} generated\n"
                f"**⏱️ Generation Time:** `{generation_time:.2f}s`\n"
                f"**⏰ Timestamp:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            )

            if seed:
                log_message += f"**🌱 Seed:** `{seed}`\n"

            log_message += f"\n**📝 Prompt:**\n```{safe_prompt}```"

            # Add quality indicators
            if generation_time < 10:
                log_message += "\n\n⚡ *Fast generation*"
            elif generation_time > 30:
                log_message += "\n\n🐌 *Slow generation - complex prompt*"

            # Send the main log message
            success = await self._send_log_message(log_message, priority="high")

            if success and image_urls:
                # Send image URLs as separate messages
                for i, url in enumerate(image_urls, 1):
                    image_message = (
                        f"🖼️ **Image {i}/{len(image_urls)}**\n"
                        f"**Direct Link:** [View Image]({url})\n"
                        f"**Model:** {model.upper()} | **User:** @{safe_username}"
                    )
                    await self._send_log_message(image_message, retry_count=1)
                    await asyncio.sleep(0.3)  # Small delay between messages

        except Exception as e:
            logger.error(f"Failed to log image generation: {e}")
            self.stats["last_error"] = f"Image logging failed: {str(e)}"

    async def log_user_action(self, user_id: int, username: str, action: str, action_type: str, 
                            details: Optional[str] = None):
        """Log user actions with enhanced context"""
        try:
            safe_username = self._escape_markdown(username)
            safe_action = self._escape_markdown(action)
            safe_details = self._escape_markdown(details) if details else None

            log_message = (
                f"👤 **USER ACTION**\n\n"
                f"**User:** @{safe_username} (`{user_id}`)\n"
                f"**Action:** `{safe_action}`\n"
                f"**Type:** `{action_type}`\n"
                f"**Time:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            )

            if safe_details:
                log_message += f"**Details:** `{safe_details}`\n"

            # Add context based on action type
            if action_type == "Command":
                log_message += "\n🔧 *Bot command executed*"
            elif action_type == "Image Generation Request":
                log_message += "\n🎨 *Image generation initiated*"

            await self._send_log_message(log_message, priority="normal")

        except Exception as e:
            logger.error(f"Failed to log user action: {e}")

    async def log_admin_action(self, admin_id: int, action: str, target_user: Optional[int] = None, 
                             details: Optional[str] = None, success: bool = True):
        """Log admin actions with enhanced tracking"""
        try:
            safe_action = self._escape_markdown(action)
            safe_details = self._escape_markdown(details) if details else None

            status_emoji = "✅" if success else "❌"

            log_message = (
                f"🔧 **ADMIN ACTION** {status_emoji}\n\n"
                f"**Admin:** `{admin_id}`\n"
                f"**Action:** `{safe_action}`\n"
                f"**Status:** {'Success' if success else 'Failed'}\n"
            )

            if target_user:
                log_message += f"**Target User:** `{target_user}`\n"

            if safe_details:
                log_message += f"**Details:** `{safe_details}`\n"

            log_message += f"**Time:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"

            # Add severity indicator
            if "ban" in action.lower() or "remove" in action.lower():
                log_message += "\n⚠️ *High-impact admin action*"

            await self._send_log_message(log_message, priority="high")

        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")

    async def log_system_event(self, event: str, event_type: str, severity: str = "info", 
                             context: Optional[Dict[str, Any]] = None):
        """Log system events with enhanced metadata"""
        try:
            safe_event = self._escape_markdown(event)

            # Choose emoji based on event type and severity
            emoji_map = {
                "STARTUP": "🚀",
                "SHUTDOWN": "🔴",
                "ERROR": "❌",
                "WARNING": "⚠️",
                "INFO": "ℹ️",
                "SUCCESS": "✅"
            }

            emoji = emoji_map.get(event_type, "🤖")

            log_message = (
                f"{emoji} **SYSTEM EVENT**\n\n"
                f"**Event:** `{safe_event}`\n"
                f"**Type:** `{event_type}`\n"
                f"**Severity:** `{severity.upper()}`\n"
                f"**Time:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            )

            if context:
                log_message += f"**Context:** `{json.dumps(context, indent=2)}`\n"

            # Add uptime for certain events
            if event_type in ["STARTUP", "SHUTDOWN"]:
                uptime = datetime.utcnow() - self.stats["start_time"]
                log_message += f"**Uptime:** `{self._format_timedelta(uptime)}`\n"

            priority = "high" if severity in ["error", "critical"] else "normal"
            await self._send_log_message(log_message, priority=priority)

        except Exception as e:
            logger.error(f"Failed to log system event: {e}")

    async def log_error(self, error: str, user_id: Optional[int] = None, context: Optional[str] = None, 
                       traceback_info: Optional[str] = None):
        """Log errors with comprehensive debugging information"""
        try:
            safe_error = self._escape_markdown(error)
            safe_context = self._escape_markdown(context) if context else None

            log_message = (
                f"❌ **ERROR REPORT**\n\n"
                f"**Error:** `{safe_error}`\n"
                f"**Time:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            )

            if user_id:
                log_message += f"**User ID:** `{user_id}`\n"

            if safe_context:
                log_message += f"**Context:** `{safe_context}`\n"

            # Add error frequency tracking
            error_count = getattr(self, '_error_count', {})
            error_hash = hash(error)
            error_count[error_hash] = error_count.get(error_hash, 0) + 1
            self._error_count = error_count

            if error_count[error_hash] > 1:
                log_message += f"**Frequency:** `{error_count[error_hash]} times`\n"

            log_message += "\n🔍 *Requires investigation*"

            await self._send_log_message(log_message, priority="high")

            # Send traceback as separate message if available
            if traceback_info:
                traceback_message = (
                    f"📋 **TRACEBACK INFO**\n\n"
                    f"```python\n{traceback_info[:3000]}```"  # Limit length
                )
                await self._send_log_message(traceback_message, priority="normal")

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    async def log_bot_statistics(self, stats: Dict[str, Any], period: str = "daily"):
        """Log comprehensive bot statistics"""
        try:
            stats_message = (
                f"📊 **{period.upper()} STATISTICS REPORT**\n\n"

                f"**👥 User Metrics:**\n"
                f"• Total Authorized: `{stats.get('total_users', 0)}`\n"
                f"• Active (7 days): `{stats.get('active_users_7d', 0)}`\n"
                f"• Banned Users: `{stats.get('total_banned', 0)}`\n\n"

                f"**🎨 Generation Metrics:**\n"
                f"• Total Generations: `{stats.get('total_generations', 0)}`\n"
                f"• Recent (24h): `{stats.get('recent_generations_24h', 0)}`\n"
                f"• Average per User: `{stats.get('avg_generations_per_user', 0):.1f}`\n\n"

                f"**📈 Performance:**\n"
                f"• Success Rate: `{stats.get('success_rate', 0):.1f}%`\n"
                f"• Avg Generation Time: `{stats.get('avg_generation_time', 0):.1f}s`\n"
                f"• Error Rate: `{stats.get('error_rate', 0):.1f}%`\n\n"

                f"**📱 Popular Features:**\n"
                f"• Most Used Model: `{stats.get('popular_model', 'N/A')}`\n"
                f"• Most Used Ratio: `{stats.get('popular_ratio', 'N/A')}`\n"
                f"• Peak Usage Hour: `{stats.get('peak_hour', 'N/A')}`\n\n"

                f"**🤖 System Status:**\n"
                f"• Messages Sent: `{self.stats['messages_sent']}`\n"
                f"• Messages Failed: `{self.stats['messages_failed']}`\n"
                f"• Uptime: `{self._format_timedelta(datetime.utcnow() - self.stats['start_time'])}`\n\n"

                f"**📅 Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            await self._send_log_message(stats_message, priority="normal")

        except Exception as e:
            logger.error(f"Failed to log statistics: {e}")

    def _escape_markdown(self, text: str) -> str:
        """Escape markdown characters to prevent parsing errors"""
        if not text:
            return ""

        # Characters that need escaping in Telegram markdown
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!', '\\']

        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _get_ratio_size(self, aspect_ratio: str) -> str:
        """Get size string for aspect ratio"""
        size_mapping = {
            "landscape": "1344x768",
            "portrait": "768x1344",
            "square": "1024x1024",
            "wide": "1344x576",
            "cinema": "1344x572",
            "photo": "1024x768"
        }
        return size_mapping.get(aspect_ratio, "1024x1024")

    def _format_timedelta(self, td: timedelta) -> str:
        """Format timedelta for display"""
        total_seconds = int(td.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    async def get_logger_stats(self) -> Dict[str, Any]:
        """Get comprehensive logger statistics"""
        return {
            "is_initialized": self.is_initialized,
            "messages_sent": self.stats["messages_sent"],
            "messages_failed": self.stats["messages_failed"],
            "failed_queue_size": len(self.failed_messages),
            "last_error": self.stats["last_error"],
            "uptime": self._format_timedelta(datetime.utcnow() - self.stats["start_time"]),
            "success_rate": (self.stats["messages_sent"] / max(1, self.stats["messages_sent"] + self.stats["messages_failed"])) * 100
        }

    async def close(self):
        """Gracefully close the logger client"""
        try:
            if self.log_client:
                # Send shutdown message
                shutdown_message = (
                    f"🔴 **MedusaXD Logger Shutdown**\n\n"
                    f"**Shutdown Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                    f"**Total Messages Sent:** `{self.stats['messages_sent']}`\n"
                    f"**Messages Failed:** `{self.stats['messages_failed']}`\n"
                    f"**Uptime:** `{self._format_timedelta(datetime.utcnow() - self.stats['start_time'])}`\n\n"
                    "📋 **Session Summary Complete**"
                )

                await self._send_log_message(shutdown_message, priority="high")
                await asyncio.sleep(1)  # Give time for message to send

                await self.log_client.stop()
                self.is_initialized = False
                logger.info("🔴 Logger client stopped gracefully")
        except Exception as e:
            logger.error(f"Error closing logger: {e}")
