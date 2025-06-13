"""
MedusaXD Image Generator Bot - Hydrogram Version
A comprehensive Telegram bot for AI image generation with admin controls and logging.
"""

import asyncio
import logging
from datetime import datetime
from hydrogram import Client, filters
from hydrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

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

        # Initialize Hydrogram client
        self.app = Client(
            "medusaxd_bot",
            bot_token=self.config.BOT_TOKEN,
            api_id=self.config.API_ID,  # You'll need to get this from my.telegram.org
            api_hash=self.config.API_HASH  # You'll need to get this from my.telegram.org
        )

    async def initialize(self):
        """Initialize the bot and database"""
        try:
            await self.db.connect()
            logger.info("Database connected successfully")

            # Add default admin if not exists
            if self.config.ADMIN_IDS:
                for admin_id in self.config.ADMIN_IDS:
                    await self.db.add_admin(admin_id)
                    await self.db.add_authorized_user(admin_id)

            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    # Command handlers
    @staticmethod
    async def start_command(client: Client, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

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

        await message.reply_text(welcome_message)

    async def generate_command(self, client: Client, message: Message):
        """Handle /generate command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        # Check permissions
        if not await self._check_user_permissions(message, user_id, username):
            return

        # Get prompt
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **No prompt provided**\n\n"
                "**Usage:** `/generate Your amazing prompt here`\n\n"
                "**Example:** `/generate A beautiful sunset over mountains`"
            )
            return

        prompt = " ".join(message.command[1:])

        # Check rate limit
        if not await self.db.check_rate_limit(user_id, self.config.RATE_LIMIT_MINUTES, self.config.MAX_REQUESTS_PER_PERIOD):
            await message.reply_text(
                f"⏳ **Rate limit exceeded**\n\n"
                f"You can make {self.config.MAX_REQUESTS_PER_PERIOD} requests every {self.config.RATE_LIMIT_MINUTES} minutes.\n"
                "Please wait before making another request."
            )
            return

        # Record request for rate limiting
        await self.db.record_request(user_id)

        # Send processing message
        processing_msg = await message.reply_text(
            f"🎨 **Generating image...**\n\n"
            f"**Prompt:** {prompt}\n\n"
            "⏳ *This may take a few moments...*"
        )

        try:
            # Generate image using your existing image generator
            response = await self.command_handler.image_generator.generate_images(
                prompt=prompt,
                model="img3",
                num_images=1,
                aspect_ratio="landscape"
            )

            # Delete processing message
            await processing_msg.delete()

            # Send generated image
            image_url = response.data[0].url
            caption = (
                f"🎨 **MedusaXD Generated Image**\n\n"
                f"**Prompt:** {prompt}\n"
                f"**Generated by:** @{username} (`{user_id}`)"
            )

            await message.reply_photo(photo=image_url, caption=caption)

            # Update statistics and log
            await self.db.increment_user_generations(user_id)
            await self.db.log_generation(user_id, username, prompt, "img3", [image_url], True)
            await self.bot_logger.log_image_generation(user_id, username, prompt, "img3", "landscape", [image_url])

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            await processing_msg.edit_text(
                f"❌ **Image generation failed**\n\n"
                f"**Error:** {str(e)}\n\n"
                "Please try again with a different prompt."
            )

    async def _check_user_permissions(self, message: Message, user_id: int, username: str) -> bool:
        """Check if user has permissions"""
        # Check if bot is enabled
        bot_status = await self.db.get_bot_status()
        if not bot_status.get('enabled', True):
            await message.reply_text("🚫 **MedusaXD Bot is currently disabled.**")
            return False

        # Check if user is authorized
        if not await self.db.is_user_authorized(user_id):
            await message.reply_text(
                "🔒 **Access Denied**\n\n"
                "You are not authorized to use MedusaXD Image Generator Bot."
            )
            return False

        # Check if user is banned
        if await self.db.is_user_banned(user_id):
            ban_info = await self.db.get_ban_info(user_id)
            await message.reply_text(
                f"🚫 **You are banned from using this bot**\n\n"
                f"**Reason:** {ban_info.get('reason', 'No reason provided')}"
            )
            return False

        return True

    def setup_handlers(self):
        """Setup all command handlers"""
        # Basic commands
        self.app.on_message(filters.command("start"))(self.start_command)
        self.app.on_message(filters.command("generate"))(self.generate_command)
        self.app.on_message(filters.command("help"))(self.command_handler.help_command)
        self.app.on_message(filters.command("models"))(self.command_handler.models_command)
        self.app.on_message(filters.command("profile"))(self.command_handler.profile_command)

        # Admin commands
        self.app.on_message(filters.command("admin"))(self.admin_handler.admin_panel)
        self.app.on_message(filters.command("adduser"))(self.admin_handler.add_user)
        self.app.on_message(filters.command("removeuser"))(self.admin_handler.remove_user)
        self.app.on_message(filters.command("ban"))(self.admin_handler.ban_user)
        self.app.on_message(filters.command("unban"))(self.admin_handler.unban_user)
        self.app.on_message(filters.command("broadcast"))(self.admin_handler.broadcast)
        self.app.on_message(filters.command("stats"))(self.admin_handler.stats)

        # Callback query handler
        self.app.on_callback_query()(self.admin_handler.button_callback)

    async def run(self):
        """Run the bot"""
        try:
            await self.initialize()
            self.setup_handlers()

            await self.bot_logger.log_system_event("Bot started successfully", "STARTUP")
            logger.info("🚀 MedusaXD Bot is starting...")

            await self.app.start()
            logger.info("✅ Bot is running!")

            # Keep the bot running
            await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            await self.bot_logger.log_system_event(f"Bot startup failed: {e}", "ERROR")
            raise
        finally:
            await self.app.stop()

async def main():
    """Main entry point"""
    bot = MedusaXDBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
