"""
MedusaXD Image Generator Bot
A comprehensive Telegram bot for AI image generation with admin controls and logging.
"""

import logging
import os
import sys
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Updater,
    CommandHandler, 
    MessageHandler, 
    Filters, 
    CallbackContext,
    CallbackQueryHandler
)
from telegram.error import TelegramError

from config import Config
from database import Database
from admin import AdminHandler
from commands import CommandHandler as BotCommands
from logger import BotLogger

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MedusaXDBot:
    def __init__(self):
        self.config = Config()
        self.db = None
        self.bot_logger = None
        self.admin_handler = None
        self.command_handler = None

    async def initialize_async_components(self):
        """Initialize async components"""
        self.db = Database(self.config.MONGODB_URL)
        await self.db.connect()

        self.bot_logger = BotLogger(self.config.BOT_TOKEN, self.config.LOG_CHANNEL_ID)
        self.admin_handler = AdminHandler(self.db, self.bot_logger, self.config)
        self.command_handler = BotCommands(self.db, self.bot_logger, self.config)

        # Add default admin if not exists
        if self.config.ADMIN_IDS:
            for admin_id in self.config.ADMIN_IDS:
                await self.db.add_admin(admin_id)
                await self.db.add_authorized_user(admin_id)

        logger.info("Bot initialized successfully")

    def start_command(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        # Use a simple synchronous approach for v13.x
        welcome_message = (
            "🎨 *Welcome to MedusaXD Image Generator Bot!*\n\n"
            "Generate stunning AI images with simple text prompts!\n\n"
            "*Available Commands:*\n"
            "🖼️ `/generate <prompt>` - Generate an image\n"
            "📊 `/models` - View available AI models\n"
            "ℹ️ `/help` - Get detailed help\n"
            "👤 `/profile` - View your profile\n\n"
            "*Example:*\n"
            "`/generate A majestic dragon flying over a crystal castle at sunset`\n\n"
            "✨ _Let your imagination run wild!_"
        )

        update.message.reply_text(welcome_message, parse_mode='Markdown')

    def error_handler(self, update: object, context: CallbackContext):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

        if update and hasattr(update, 'effective_message'):
            try:
                update.effective_message.reply_text(
                    "❌ *An error occurred while processing your request.*\n\n"
                    "Please try again later or contact an administrator.",
                    parse_mode='Markdown'
                )
            except:
                pass

    def run(self):
        """Run the bot using v13.x pattern"""
        try:
            # Initialize async components first
            import asyncio
            asyncio.run(self.initialize_async_components())

            # Create updater
            updater = Updater(token=self.config.BOT_TOKEN, use_context=True)
            dispatcher = updater.dispatcher

            # Add handlers
            dispatcher.add_handler(CommandHandler("start", self.start_command))
            dispatcher.add_handler(CommandHandler("help", self.command_handler.help_command_sync))
            dispatcher.add_handler(CommandHandler("generate", self.command_handler.generate_command_sync))
            dispatcher.add_handler(CommandHandler("models", self.command_handler.models_command_sync))
            dispatcher.add_handler(CommandHandler("profile", self.command_handler.profile_command_sync))

            # Admin commands
            dispatcher.add_handler(CommandHandler("admin", self.admin_handler.admin_panel_sync))
            dispatcher.add_handler(CommandHandler("adduser", self.admin_handler.add_user_sync))
            dispatcher.add_handler(CommandHandler("removeuser", self.admin_handler.remove_user_sync))
            dispatcher.add_handler(CommandHandler("ban", self.admin_handler.ban_user_sync))
            dispatcher.add_handler(CommandHandler("unban", self.admin_handler.unban_user_sync))
            dispatcher.add_handler(CommandHandler("broadcast", self.admin_handler.broadcast_sync))
            dispatcher.add_handler(CommandHandler("botstatus", self.admin_handler.bot_status_sync))
            dispatcher.add_handler(CommandHandler("users", self.admin_handler.list_users_sync))
            dispatcher.add_handler(CommandHandler("stats", self.admin_handler.stats_sync))

            # Callback query handler
            dispatcher.add_handler(CallbackQueryHandler(self.admin_handler.button_callback_sync))

            # Error handler
            dispatcher.add_error_handler(self.error_handler)

            # Set bot commands
            try:
                updater.bot.set_my_commands([
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get help and usage instructions"),
                    BotCommand("generate", "Generate an AI image"),
                    BotCommand("models", "View available AI models"),
                    BotCommand("profile", "View your profile"),
                ])
                logger.info("Bot commands menu set successfully")
            except Exception as e:
                logger.error(f"Failed to set bot commands: {e}")

            # Log bot startup
            asyncio.run(self.bot_logger.log_system_event("Bot started successfully", "STARTUP"))

            logger.info("🚀 MedusaXD Bot is starting...")

            # Start polling - This should work with v13.x
            updater.start_polling()
            logger.info("✅ Bot is running! Press Ctrl+C to stop.")
            updater.idle()

        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            try:
                import asyncio
                asyncio.run(self.bot_logger.log_system_event(f"Bot startup failed: {e}", "ERROR"))
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    bot = MedusaXDBot()
    bot.run()
