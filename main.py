"""
MedusaXD Image Generator Bot
A comprehensive Telegram bot for AI image generation with admin controls and logging.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
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
        self.db = Database(self.config.MONGODB_URL)
        self.bot_logger = BotLogger(self.config.BOT_TOKEN, self.config.LOG_CHANNEL_ID)
        self.admin_handler = AdminHandler(self.db, self.bot_logger, self.config)
        self.command_handler = BotCommands(self.db, self.bot_logger, self.config)

    async def initialize(self):
        """Initialize the bot and database"""
        try:
            await self.db.connect()
            logger.info("✅ Database connected successfully")

            # Add default admin if not exists
            if self.config.ADMIN_IDS:
                for admin_id in self.config.ADMIN_IDS:
                    await self.db.add_admin(admin_id)
                    await self.db.add_authorized_user(admin_id)

            logger.info("✅ Bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            sys.exit(1)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        # Log user interaction
        await self.bot_logger.log_user_action(user_id, username, "/start", "Command")

        # Check if bot is enabled
        bot_status = await self.db.get_bot_status()
        if not bot_status.get('enabled', True):
            await update.message.reply_text(
                "🚫 **MedusaXD Bot is currently disabled.**\n\n"
                "Please try again later.",
                parse_mode='Markdown'
            )
            return

        # Check if user is authorized
        if not await self.db.is_user_authorized(user_id):
            await update.message.reply_text(
                "🔒 **Access Denied**\n\n"
                "You are not authorized to use MedusaXD Image Generator Bot.\n"
                "Please contact an administrator for access.",
                parse_mode='Markdown'
            )
            return

        # Check if user is banned
        if await self.db.is_user_banned(user_id):
            ban_info = await self.db.get_ban_info(user_id)
            await update.message.reply_text(
                f"🚫 **You are banned from using this bot**\n\n"
                f"**Reason:** {ban_info.get('reason', 'No reason provided')}\n"
                f"**Banned on:** {ban_info.get('banned_at', 'Unknown')}\n\n"
                "Contact an administrator if you believe this is an error.",
                parse_mode='Markdown'
            )
            return

        welcome_message = (
            "🎨 **Welcome to MedusaXD Image Generator Bot!**\n\n"
            "Generate stunning AI images with simple text prompts!\n\n"
            "**Available Commands:**\n"
            "🖼️ `/generate <prompt>` - Generate an image\n"
            "📊 `/models` - View available AI models\n"
            "ℹ️ `/help` - Get detailed help\n"
            "👤 `/profile` - View your profile\n\n"
            "**Example:**\n"
            "`/generate A majestic dragon flying over a crystal castle at sunset`\n\n"
            "✨ *Let your imagination run wild!*"
        )

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

        if update and hasattr(update, 'effective_message'):
            try:
                await update.effective_message.reply_text(
                    "❌ **An error occurred while processing your request.**\n\n"
                    "Please try again later or contact an administrator.",
                    parse_mode='Markdown'
                )
            except:
                pass

    def setup_handlers(self, app: Application):
        """Setup all command handlers"""
        # Basic commands
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.command_handler.help_command))
        app.add_handler(CommandHandler("generate", self.command_handler.generate_command))
        app.add_handler(CommandHandler("models", self.command_handler.models_command))
        app.add_handler(CommandHandler("profile", self.command_handler.profile_command))

        # Admin commands
        app.add_handler(CommandHandler("admin", self.admin_handler.admin_panel))
        app.add_handler(CommandHandler("adduser", self.admin_handler.add_user))
        app.add_handler(CommandHandler("removeuser", self.admin_handler.remove_user))
        app.add_handler(CommandHandler("ban", self.admin_handler.ban_user))
        app.add_handler(CommandHandler("unban", self.admin_handler.unban_user))
        app.add_handler(CommandHandler("broadcast", self.admin_handler.broadcast))
        app.add_handler(CommandHandler("botstatus", self.admin_handler.bot_status))
        app.add_handler(CommandHandler("users", self.admin_handler.list_users))
        app.add_handler(CommandHandler("stats", self.admin_handler.stats))

        # Callback query handler for admin panel buttons
        app.add_handler(CallbackQueryHandler(self.admin_handler.button_callback))

        # Error handler
        app.add_error_handler(self.error_handler)

    async def setup_bot_commands(self, app: Application):
        """Setup bot command menu"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help and usage instructions"),
            BotCommand("generate", "Generate an AI image"),
            BotCommand("models", "View available AI models"),
            BotCommand("profile", "View your profile"),
        ]

        try:
            await app.bot.set_my_commands(commands)
            logger.info("✅ Bot commands menu set successfully")
        except Exception as e:
            logger.error(f"❌ Failed to set bot commands: {e}")

    async def run(self):
        """Run the bot"""
        try:
            # Initialize the bot
            await self.initialize()

            # Create application
            app = Application.builder().token(self.config.BOT_TOKEN).build()

            # Setup handlers
            self.setup_handlers(app)

            # Setup bot commands menu
            await self.setup_bot_commands(app)

            # Log bot startup
            await self.bot_logger.log_system_event("Bot started successfully", "STARTUP")

            logger.info("🚀 MedusaXD Bot is starting...")

            # Start polling (background worker mode)
            await app.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )

        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            await self.bot_logger.log_system_event(f"Bot startup failed: {e}", "ERROR")
            sys.exit(1)

if __name__ == "__main__":
    bot = MedusaXDBot()
    asyncio.run(bot.run())
