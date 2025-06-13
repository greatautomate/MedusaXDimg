"""
MedusaXD Image Generator Bot - AIWorldCreator API Version
A comprehensive Telegram bot for AI image generation with admin controls and logging.
"""

import asyncio
import logging
from datetime import datetime
from hydrogram import Client, filters
from hydrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from database import Database
from infip_provider import MedusaXDImageGenerator

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
        self.image_generator = MedusaXDImageGenerator()

        # Initialize Hydrogram client
        self.app = Client(
            "medusaxd_bot",
            bot_token=self.config.BOT_TOKEN,
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH
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

    async def start_command(self, client: Client, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        # Check permissions
        if not await self._check_user_permissions(message, user_id, username):
            return

        welcome_message = (
            "🎨 **Welcome to MedusaXD Image Generator Bot!**\n\n"
            "Generate stunning AI images with simple text prompts!\n\n"
            "**🚀 Available Commands:**\n"
            "🖼️ `/generate <prompt>` - Generate an image\n"
            "🤖 `/models` - View available AI models\n"
            "ℹ️ `/help` - Get detailed help\n"
            "👤 `/profile` - View your profile\n"
            "🎨 `/quick <prompt>` - Quick generation (turbo model)\n"
            "✨ `/flux <prompt>` - High-quality generation (flux model)\n"
            "🎭 `/creative <prompt>` - Creative generation (gptimage model)\n\n"
            "**📐 Advanced Options:**\n"
            "🖼️ `/portrait <prompt>` - Portrait orientation\n"
            "🖼️ `/landscape <prompt>` - Landscape orientation\n"
            "🖼️ `/square <prompt>` - Square orientation\n\n"
            "**Example:**\n"
            "`/generate A majestic dragon flying over a crystal castle at sunset`\n\n"
            "✨ *Let your imagination run wild with MedusaXD!*"
        )

        await message.reply_text(welcome_message)

    async def generate_command(self, client: Client, message: Message):
        """Handle /generate command with model selection"""
        await self._handle_generation(message, model="turbo", aspect_ratio="landscape")

    async def quick_command(self, client: Client, message: Message):
        """Handle /quick command - fast turbo generation"""
        await self._handle_generation(message, model="turbo", aspect_ratio="square")

    async def flux_command(self, client: Client, message: Message):
        """Handle /flux command - high quality generation"""
        await self._handle_generation(message, model="flux", aspect_ratio="landscape")

    async def creative_command(self, client: Client, message: Message):
        """Handle /creative command - creative GPT generation"""
        await self._handle_generation(message, model="gptimage", aspect_ratio="portrait")

    async def portrait_command(self, client: Client, message: Message):
        """Handle /portrait command - portrait orientation"""
        await self._handle_generation(message, model="turbo", aspect_ratio="portrait")

    async def landscape_command(self, client: Client, message: Message):
        """Handle /landscape command - landscape orientation"""
        await self._handle_generation(message, model="flux", aspect_ratio="landscape")

    async def square_command(self, client: Client, message: Message):
        """Handle /square command - square orientation"""
        await self._handle_generation(message, model="turbo", aspect_ratio="square")

    async def _handle_generation(self, message: Message, model: str, aspect_ratio: str):
        """Generic image generation handler"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        # Check permissions
        if not await self._check_user_permissions(message, user_id, username):
            return

        # Get prompt
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            await message.reply_text(
                f"❌ **No prompt provided**\n\n"
                f"**Usage:** `{command_parts[0]} Your amazing prompt here`\n\n"
                f"**Example:** `{command_parts[0]} A beautiful sunset over mountains`\n\n"
                f"**Model:** {model.title()} | **Aspect:** {aspect_ratio.title()}"
            )
            return

        prompt = command_parts[1]

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

        # Get model info for display
        model_info = self.image_generator.get_model_info()
        model_name = model_info.get(model, {}).get("name", model.title())

        # Send processing message
        processing_msg = await message.reply_text(
            f"🎨 **Generating image with {model_name}...**\n\n"
            f"**📝 Prompt:** {prompt}\n"
            f"**🤖 Model:** {model_name}\n"
            f"**📐 Aspect:** {aspect_ratio.title()}\n\n"
            "⏳ *This may take a few moments...*"
        )

        try:
            # Test API connection first
            if not await self.image_generator.test_connection():
                await processing_msg.edit_text(
                    "❌ **Image generation service temporarily unavailable**\n\n"
                    "🔧 The AI image generation API is currently experiencing issues.\n"
                    "Please try again in a few minutes."
                )
                return

            # Generate image
            response = await self.image_generator.generate_images(
                prompt=prompt,
                model=model,
                num_images=1,
                aspect_ratio=aspect_ratio,
                style="realistic"
            )

            # Delete processing message
            await processing_msg.delete()

            # Send generated image
            image_url = response.data[0].url
            caption = (
                f"🎨 **MedusaXD Generated Image**\n\n"
                f"**📝 Prompt:** {prompt}\n"
                f"**🤖 Model:** {model_name}\n"
                f"**📐 Aspect:** {aspect_ratio.title()}\n"
                f"**👤 Generated by:** @{username}"
            )

            await message.reply_photo(photo=image_url, caption=caption)

            # Update statistics and log
            await self.db.increment_user_generations(user_id)
            await self.db.log_generation(user_id, username, prompt, model, [image_url], True)

        except ValueError as e:
            await processing_msg.edit_text(
                f"❌ **Invalid input**\n\n"
                f"**Error:** {str(e)}\n\n"
                "Please check your prompt and try again."
            )
        except RuntimeError as e:
            error_msg = str(e)
            if "Model" in error_msg and "not supported" in error_msg:
                await processing_msg.edit_text(
                    f"❌ **Model Error**\n\n"
                    f"**Error:** {error_msg}\n\n"
                    "Available models: flux, turbo, gptimage"
                )
            else:
                await processing_msg.edit_text(
                    f"❌ **Generation failed**\n\n"
                    f"**Error:** {error_msg}\n\n"
                    "Please try again with a different prompt."
                )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await processing_msg.edit_text(
                "❌ **Unexpected error occurred**\n\n"
                "Please try again later or contact an administrator."
            )

    async def help_command(self, client: Client, message: Message):
        """Handle /help command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        if not await self._check_user_permissions(message, user_id, username):
            return

        help_text = (
            "🎨 **MedusaXD Image Generator Bot - Complete Guide**\n\n"

            "**🖼️ Basic Generation Commands:**\n"
            "• `/generate <prompt>` - Standard generation (turbo model)\n"
            "• `/quick <prompt>` - Fast generation (square format)\n"
            "• `/flux <prompt>` - High-quality generation (landscape)\n"
            "• `/creative <prompt>` - Creative AI generation (portrait)\n\n"

            "**📐 Orientation Commands:**\n"
            "• `/portrait <prompt>` - Vertical/Portrait format (9:16)\n"
            "• `/landscape <prompt>` - Horizontal/Landscape format (16:9)\n"
            "• `/square <prompt>` - Square format (1:1)\n\n"

            "**🤖 Available AI Models:**\n"
            "• **Flux** - Professional quality, detailed artwork\n"
            "• **Turbo** - Fast generation, good quality\n"
            "• **GPTImage** - Creative AI, concept art\n\n"

            "**📊 User Commands:**\n"
            "• `/models` - View detailed model information\n"
            "• `/profile` - View your profile and stats\n"
            "• `/help` - Show this help message\n\n"

            "**🎯 Example Prompts:**\n"
            "• `/flux A majestic dragon in a fantasy landscape, highly detailed`\n"
            "• `/quick A cute robot character, cartoon style`\n"
            "• `/creative Abstract art with vibrant colors and flowing shapes`\n"
            "• `/portrait A wise wizard with a long beard, fantasy art`\n\n"

            f"**⏱️ Rate Limits:**\n"
            f"• Max {self.config.MAX_REQUESTS_PER_PERIOD} requests per {self.config.RATE_LIMIT_MINUTES} minutes\n\n"

            "**💡 Pro Tips:**\n"
            "• Be descriptive in your prompts\n"
            "• Specify art style, lighting, mood\n"
            "• Use quality keywords like 'detailed', 'high resolution'\n"
            "• Try different models for different styles\n\n"

            "✨ *Unleash your creativity with MedusaXD!*"
        )

        await message.reply_text(help_text)

    async def models_command(self, client: Client, message: Message):
        """Handle /models command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        if not await self._check_user_permissions(message, user_id, username):
            return

        model_info = self.image_generator.get_model_info()

        models_text = (
            "🤖 **Available AI Models**\n\n"

            "**✨ Flux** - *Professional Quality*\n"
            f"• {model_info['flux']['description']}\n"
            f"• Best for: {model_info['flux']['best_for']}\n"
            "• Command: `/flux <prompt>`\n\n"

            "**⚡ Turbo** - *Fast & Reliable*\n"
            f"• {model_info['turbo']['description']}\n"
            f"• Best for: {model_info['turbo']['best_for']}\n"
            "• Commands: `/quick <prompt>`, `/generate <prompt>`\n\n"

            "**🎭 GPTImage** - *Creative AI*\n"
            f"• {model_info['gptimage']['description']}\n"
            f"• Best for: {model_info['gptimage']['best_for']}\n"
            "• Command: `/creative <prompt>`\n\n"

            f"**🎯 Default Model:** {self.config.DEFAULT_MODEL.title()}\n\n"

            "**📐 Available Formats:**\n"
            "• Portrait (9:16) - `/portrait <prompt>`\n"
            "• Landscape (16:9) - `/landscape <prompt>`\n"
            "• Square (1:1) - `/square <prompt>`\n\n"

            "**💡 Model Selection Guide:**\n"
            "• Use **Flux** for detailed, professional artwork\n"
            "• Use **Turbo** for quick prototypes and general use\n"
            "• Use **GPTImage** for creative and abstract art\n\n"

            "**⚙️ Technical Specs:**\n"
            "• All models support 1024x1024+ resolution\n"
            "• PNG format output\n"
            "• Seed control for reproducibility\n"
            "• Style customization available"
        )

        await message.reply_text(models_text)

    async def profile_command(self, client: Client, message: Message):
        """Handle /profile command"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        if not await self._check_user_permissions(message, user_id, username):
            return

        # Get user data
        users = await self.db.get_authorized_users()
        user_data = next((u for u in users if u['user_id'] == user_id), None)

        if not user_data:
            await message.reply_text("❌ **Profile not found**")
            return

        # Check rate limit status
        can_generate = await self.db.check_rate_limit(
            user_id, 
            self.config.RATE_LIMIT_MINUTES, 
            self.config.MAX_REQUESTS_PER_PERIOD
        )

        profile_text = (
            f"👤 **Profile: {username}**\n\n"

            f"**📊 Statistics:**\n"
            f"• User ID: `{user_id}`\n"
            f"• Total Generations: `{user_data.get('total_generations', 0)}`\n"
            f"• Member Since: `{user_data.get('authorized_at', 'Unknown').strftime('%Y-%m-%d') if user_data.get('authorized_at') else 'Unknown'}`\n\n"

            f"**⚡ Rate Limit Status:**\n"
            f"• Status: {'✅ Available' if can_generate else '⏳ Limited'}\n"
            f"• Limit: {self.config.MAX_REQUESTS_PER_PERIOD} requests per {self.config.RATE_LIMIT_MINUTES} minutes\n\n"

            f"**🎨 Quick Commands:**\n"
            f"• `/flux your prompt` - High quality\n"
            f"• `/quick your prompt` - Fast generation\n"
            f"• `/creative your prompt` - Creative AI\n\n"

            "**🚀 Ready to create amazing images!**"
        )

        await message.reply_text(profile_text)

    async def admin_command(self, client: Client, message: Message):
        """Handle /admin command"""
        user_id = message.from_user.id

        if not await self.db.is_admin(user_id):
            await message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        # Get statistics
        stats = await self.db.get_stats()
        bot_status = await self.db.get_bot_status()

        # Create admin panel with buttons
        keyboard = [
            [
                InlineKeyboardButton("👥 Users", callback_data="admin_users"),
                InlineKeyboardButton("🚫 Bans", callback_data="admin_bans")
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(
                    "🔴 Disable" if bot_status.get('enabled', True) else "✅ Enable",
                    callback_data="admin_toggle"
                ),
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
            ]
        ]

        admin_text = (
            "🔧 **MedusaXD Admin Panel**\n\n"

            f"**📊 Bot Statistics:**\n"
            f"• Status: {'✅ Enabled' if bot_status.get('enabled', True) else '🔴 Disabled'}\n"
            f"• Total Users: `{stats.get('total_users', 0)}`\n"
            f"• Banned Users: `{stats.get('total_banned', 0)}`\n"
            f"• Total Generations: `{stats.get('total_generations', 0)}`\n"
            f"• Recent (24h): `{stats.get('recent_generations_24h', 0)}`\n\n"

            "**🎛️ Available Admin Commands:**\n"
            "• `/adduser <user_id>` - Add user to authorized list\n"
            "• `/removeuser <user_id>` - Remove user authorization\n"
            "• `/ban <user_id> [reason]` - Ban user from bot\n"
            "• `/unban <user_id>` - Unban user\n"
            "• `/broadcast <message>` - Send message to all users\n"
            "• `/stats` - View detailed statistics\n"
            "• `/users` - List all authorized users\n\n"

            "**🎛️ Use the buttons below for quick actions:**"
        )

        await message.reply_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard))

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
                "You are not authorized to use MedusaXD Image Generator Bot.\n"
                "Please contact an administrator for access."
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

        # Update user activity
        await self.db.update_user_activity(user_id, username)
        return True

    def setup_handlers(self):
        """Setup all command handlers"""
        # Register all handlers
        @self.app.on_message(filters.command("start"))
        async def start_handler(client, message):
            await self.start_command(client, message)

        @self.app.on_message(filters.command("generate"))
        async def generate_handler(client, message):
            await self.generate_command(client, message)

        @self.app.on_message(filters.command("quick"))
        async def quick_handler(client, message):
            await self.quick_command(client, message)

        @self.app.on_message(filters.command("flux"))
        async def flux_handler(client, message):
            await self.flux_command(client, message)

        @self.app.on_message(filters.command("creative"))
        async def creative_handler(client, message):
            await self.creative_command(client, message)

        @self.app.on_message(filters.command("portrait"))
        async def portrait_handler(client, message):
            await self.portrait_command(client, message)

        @self.app.on_message(filters.command("landscape"))
        async def landscape_handler(client, message):
            await self.landscape_command(client, message)

        @self.app.on_message(filters.command("square"))
        async def square_handler(client, message):
            await self.square_command(client, message)

        @self.app.on_message(filters.command("help"))
        async def help_handler(client, message):
            await self.help_command(client, message)

        @self.app.on_message(filters.command("models"))
        async def models_handler(client, message):
            await self.models_command(client, message)

        @self.app.on_message(filters.command("profile"))
        async def profile_handler(client, message):
            await self.profile_command(client, message)

        @self.app.on_message(filters.command("admin"))
        async def admin_handler(client, message):
            await self.admin_command(client, message)

    async def run(self):
        """Run the bot"""
        try:
            await self.initialize()
            self.setup_handlers()

            logger.info("🚀 MedusaXD Bot starting...")

            async with self.app:
                logger.info("✅ Bot is running!")
                await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

async def main():
    """Main entry point"""
    bot = MedusaXDBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
