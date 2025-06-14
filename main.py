"""
MedusaXD Image Generator Bot - Advanced Command Line Interface
Enhanced with flags and original model names
"""

import asyncio
import logging
import time
import re
from datetime import datetime
from hydrogram import Client, filters
from hydrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from database import Database
from infip_provider import MedusaXDImageGenerator
from logger import BotLogger

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CommandParser:
    """Advanced command line parser for image generation"""

    # Aspect ratio mappings
    ASPECT_RATIOS = {
        # Standard ratios
        "16:9": "landscape",
        "9:16": "portrait", 
        "1:1": "square",
        "4:3": "photo",
        "3:2": "classic",
        "21:9": "wide",

        # Custom ratios
        "1.618:1": "golden",
        "2.35:1": "cinema",
        "3:4": "poster",

        # Short flags
        "l": "landscape",
        "p": "portrait",
        "s": "square",
        "w": "wide",
        "c": "cinema",
        "g": "golden"
    }

    # Style mappings
    STYLES = {
        "realistic": "realistic",
        "artistic": "artistic", 
        "anime": "anime",
        "cartoon": "cartoon",
        "photographic": "photographic",
        "cinematic": "cinematic",
        "fantasy": "fantasy",
        "cyberpunk": "cyberpunk"
    }

    @staticmethod
    def parse_command(text: str) -> dict:
        """
        Parse command with flags
        Example: /flux -r16:9 -l -srealistic A beautiful girl riding a horse
        """
        parts = text.split()
        if not parts:
            return {"error": "Empty command"}

        command = parts[0]

        # Extract model from command
        model_map = {
            "/flux": "flux",
            "/turbo": "turbo", 
            "/gptimage": "gptimage",
            "/generate": "turbo"  # Default
        }

        model = model_map.get(command, "turbo")

        # Parse flags and extract prompt
        flags = []
        prompt_parts = []

        for i, part in enumerate(parts[1:], 1):
            if part.startswith('-'):
                flags.append(part)
            else:
                # Rest is the prompt
                prompt_parts = parts[i:]
                break

        prompt = " ".join(prompt_parts)

        # Parse individual flags
        parsed_flags = CommandParser._parse_flags(flags)

        return {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": parsed_flags.get("aspect_ratio", "landscape"),
            "style": parsed_flags.get("style", "realistic"),
            "num_images": parsed_flags.get("num_images", 1),
            "seed": parsed_flags.get("seed"),
            "flags": parsed_flags
        }

    @staticmethod
    def _parse_flags(flags: list) -> dict:
        """Parse individual flags"""
        result = {}

        for flag in flags:
            flag = flag.lstrip('-')

            # Ratio flag: -r16:9 or -r1:1
            if flag.startswith('r'):
                ratio = flag[1:]
                if ratio in CommandParser.ASPECT_RATIOS:
                    result["aspect_ratio"] = CommandParser.ASPECT_RATIOS[ratio]
                else:
                    result["aspect_ratio"] = "landscape"  # Default

            # Single letter flags
            elif len(flag) == 1:
                if flag in CommandParser.ASPECT_RATIOS:
                    result["aspect_ratio"] = CommandParser.ASPECT_RATIOS[flag]
                elif flag == 'h':  # High quality
                    result["quality"] = "high"
                elif flag == 'f':  # Fast
                    result["quality"] = "fast"

            # Style flag: -srealistic or -sartistic
            elif flag.startswith('s'):
                style = flag[1:]
                if style in CommandParser.STYLES:
                    result["style"] = CommandParser.STYLES[style]

            # Number of images: -n2 or -n4
            elif flag.startswith('n'):
                try:
                    num = int(flag[1:])
                    if 1 <= num <= 4:
                        result["num_images"] = num
                except ValueError:
                    pass

            # Seed: -seed12345
            elif flag.startswith('seed'):
                try:
                    result["seed"] = int(flag[4:])
                except ValueError:
                    pass

        return result

class MedusaXDBot:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.MONGODB_URL)
        self.image_generator = MedusaXDImageGenerator()
        self.bot_logger = BotLogger(self.config.BOT_TOKEN, self.config.LOG_CHANNEL_ID)

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
            await self.bot_logger.initialize(self.config.API_ID, self.config.API_HASH)

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

        await self.bot_logger.log_user_action(user_id, username, "/start", "Command")

        if not await self._check_user_permissions(message, user_id, username):
            return

        welcome_message = (
            "🎨 **Welcome to MedusaXD Image Generator Bot!**\n\n"
            "Generate stunning AI images with **advanced command-line options**!\n\n"

            "**🤖 Available Models:**\n"
            "• `/flux` - High-quality detailed generation\n"
            "• `/turbo` - Fast generation with good quality\n"
            "• `/gptimage` - Creative AI generation\n\n"

            "**📐 Aspect Ratio Flags:**\n"
            "• `-r16:9` or `-l` - Landscape (16:9)\n"
            "• `-r9:16` or `-p` - Portrait (9:16)\n"
            "• `-r1:1` or `-s` - Square (1:1)\n"
            "• `-r21:9` or `-w` - Ultra-wide (21:9)\n"
            "• `-r2.35:1` or `-c` - Cinematic (2.35:1)\n\n"

            "**🎨 Style Flags:**\n"
            "• `-srealistic` - Photorealistic style\n"
            "• `-sartistic` - Artistic style\n"
            "• `-sanime` - Anime style\n"
            "• `-scartoon` - Cartoon style\n\n"

            "**⚙️ Advanced Flags:**\n"
            "• `-n2` - Generate 2 images (1-4)\n"
            "• `-seed12345` - Use specific seed\n"
            "• `-h` - High quality mode\n"
            "• `-f` - Fast generation mode\n\n"

            "**📝 Example Commands:**\n"
            "`/flux -r16:9 -l -srealistic A beautiful girl riding a horse`\n"
            "`/turbo -s -sanime Cute robot character`\n"
            "`/gptimage -c -scinematic Epic space battle scene`\n"
            "`/flux -n3 -seed42 -p Majestic dragon portrait`\n\n"

            "✨ *Use `/help` for detailed instructions!*"
        )

        await message.reply_text(welcome_message)

    async def flux_command(self, client: Client, message: Message):
        """Handle /flux command with advanced options"""
        await self._handle_advanced_generation(message)

    async def turbo_command(self, client: Client, message: Message):
        """Handle /turbo command with advanced options"""
        await self._handle_advanced_generation(message)

    async def gptimage_command(self, client: Client, message: Message):
        """Handle /gptimage command with advanced options"""
        await self._handle_advanced_generation(message)

    async def generate_command(self, client: Client, message: Message):
        """Handle /generate command (default turbo) with advanced options"""
        await self._handle_advanced_generation(message)

    async def _handle_advanced_generation(self, message: Message):
        """Handle image generation with advanced command parsing"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        start_time = time.time()

        # Parse the command
        parsed = CommandParser.parse_command(message.text)

        if "error" in parsed:
            await message.reply_text(f"❌ **Error:** {parsed['error']}")
            return

        # Log the generation attempt
        command_name = message.text.split()[0]
        await self.bot_logger.log_user_action(user_id, username, command_name, "Advanced Image Generation")

        # Check permissions
        if not await self._check_user_permissions(message, user_id, username):
            return

        # Validate prompt
        if not parsed["prompt"] or len(parsed["prompt"]) < 3:
            await self._show_command_help(message, parsed["model"])
            return

        # Check rate limit
        if not await self.db.check_rate_limit(user_id, self.config.RATE_LIMIT_MINUTES, self.config.MAX_REQUESTS_PER_PERIOD):
            await message.reply_text(
                f"⏳ **Rate limit exceeded**\n\n"
                f"You can make {self.config.MAX_REQUESTS_PER_PERIOD} requests every {self.config.RATE_LIMIT_MINUTES} minutes."
            )
            return

        await self.db.record_request(user_id)

        # Get model info
        model_info = self.image_generator.get_model_info()
        model_name = model_info.get(parsed["model"], {}).get("name", parsed["model"].title())

        # Create detailed status message
        flags_text = []
        if parsed.get("flags"):
            for key, value in parsed["flags"].items():
                if key == "aspect_ratio":
                    flags_text.append(f"📐 {value.title()}")
                elif key == "style":
                    flags_text.append(f"🎨 {value.title()}")
                elif key == "num_images":
                    flags_text.append(f"🖼️ {value} images")
                elif key == "seed":
                    flags_text.append(f"🌱 Seed: {value}")

        processing_msg = await message.reply_text(
            f"🎨 **Generating with {model_name}...**\n\n"
            f"**📝 Prompt:** {parsed['prompt']}\n"
            f"**🤖 Model:** {model_name}\n"
            f"**⚙️ Options:** {' | '.join(flags_text) if flags_text else 'Default settings'}\n\n"
            "⏳ *Processing your request...*"
        )

        try:
            # Generate image with parsed parameters
            response = await self.image_generator.generate_images(
                prompt=parsed["prompt"],
                model=parsed["model"],
                num_images=parsed["num_images"],
                aspect_ratio=parsed["aspect_ratio"],
                style=parsed["style"],
                seed=parsed.get("seed")
            )

            generation_time = time.time() - start_time
            await processing_msg.delete()

            # Send generated images
            for i, image_data in enumerate(response.data, 1):
                caption = (
                    f"🎨 **MedusaXD Generated Image {i}/{len(response.data)}**\n\n"
                    f"**📝 Prompt:** {parsed['prompt']}\n"
                    f"**🤖 Model:** {model_name}\n"
                    f"**📐 Aspect:** {parsed['aspect_ratio'].title()}\n"
                    f"**🎨 Style:** {parsed['style'].title()}\n"
                    f"**⏱️ Time:** {generation_time:.2f}s\n"
                    f"**👤 By:** @{username}"
                )

                if parsed.get("seed"):
                    caption += f"\n**🌱 Seed:** {parsed['seed']}"

                await message.reply_photo(photo=image_data.url, caption=caption)

                if i < len(response.data):  # Small delay between multiple images
                    await asyncio.sleep(0.5)

            # Update statistics and log
            await self.db.increment_user_generations(user_id)
            await self.db.log_generation(user_id, username, parsed["prompt"], parsed["model"], [img.url for img in response.data], True)

            # Enhanced logging with flags
            await self.bot_logger.log_image_generation(
                user_id=user_id,
                username=username,
                prompt=parsed["prompt"],
                model=parsed["model"],
                aspect_ratio=parsed["aspect_ratio"],
                image_urls=[img.url for img in response.data],
                generation_time=generation_time
            )

        except Exception as e:
            generation_time = time.time() - start_time
            logger.error(f"Advanced image generation failed: {e}")

            await processing_msg.edit_text(
                f"❌ **Generation failed**\n\n"
                f"**Error:** {str(e)}\n\n"
                f"**Command:** `{message.text}`\n\n"
                "Please check your command syntax and try again."
            )

            await self.bot_logger.log_error(
                error=str(e),
                user_id=user_id,
                context=f"Advanced generation failed: {message.text}"
            )

    async def _show_command_help(self, message: Message, model: str):
        """Show specific command help"""
        help_text = (
            f"❌ **Invalid {model.upper()} command**\n\n"

            f"**Usage:** `/{model} [flags] <prompt>`\n\n"

            "**📐 Aspect Ratio Flags:**\n"
            "• `-r16:9` or `-l` - Landscape\n"
            "• `-r9:16` or `-p` - Portrait\n"
            "• `-r1:1` or `-s` - Square\n"
            "• `-r21:9` or `-w` - Ultra-wide\n\n"

            "**🎨 Style Flags:**\n"
            "• `-srealistic` - Photorealistic\n"
            "• `-sartistic` - Artistic style\n"
            "• `-sanime` - Anime style\n\n"

            "**⚙️ Other Flags:**\n"
            "• `-n2` - Generate 2 images\n"
            "• `-seed123` - Use specific seed\n\n"

            f"**Examples:**\n"
            f"`/{model} -l -srealistic A beautiful landscape`\n"
            f"`/{model} -s -sanime Cute character design`\n"
            f"`/{model} -r21:9 -n2 Epic cinematic scene`"
        )

        await message.reply_text(help_text)

    async def help_command(self, client: Client, message: Message):
        """Enhanced help command with advanced syntax"""
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"

        if not await self._check_user_permissions(message, user_id, username):
            return

        help_text = (
            "🎨 **MedusaXD Advanced Command Guide**\n\n"

            "**🤖 Available Models:**\n"
            "• `/flux` - Premium quality, detailed artwork\n"
            "• `/turbo` - Fast generation, good quality\n"
            "• `/gptimage` - Creative AI, concept art\n\n"

            "**📐 Aspect Ratio Options:**\n"
            "```\n"
            "-r16:9  or  -l    →  Landscape (1344x768)\n"
            "-r9:16  or  -p    →  Portrait (768x1344)\n"
            "-r1:1   or  -s    →  Square (1024x1024)\n"
            "-r4:3             →  Photo ratio (1024x768)\n"
            "-r21:9  or  -w    →  Ultra-wide (1344x576)\n"
            "-r2.35:1 or -c    →  Cinematic (1344x572)\n"
            "-r1.618:1 or -g   →  Golden ratio (1024x633)\n"
            "```\n\n"

            "**🎨 Style Options:**\n"
            "```\n"
            "-srealistic    →  Photorealistic\n"
            "-sartistic     →  Artistic/Painterly\n"
            "-sanime        →  Anime/Manga style\n"
            "-scartoon      →  Cartoon style\n"
            "-scinematic    →  Cinematic look\n"
            "-sfantasy      →  Fantasy art\n"
            "-scyberpunk    →  Cyberpunk aesthetic\n"
            "```\n\n"

            "**⚙️ Advanced Options:**\n"
            "```\n"
            "-n2          →  Generate 2 images (max 4)\n"
            "-seed12345   →  Use specific seed\n"
            "-h           →  High quality mode\n"
            "-f           →  Fast generation\n"
            "```\n\n"

            "**📝 Command Examples:**\n"
            "```\n"
            "/flux -l -srealistic A beautiful girl riding a horse\n"
            "/turbo -s -sanime Cute robot character\n"
            "/gptimage -c -scinematic Epic space battle\n"
            "/flux -n3 -seed42 -p Majestic dragon portrait\n"
            "/turbo -w -sfantasy Panoramic fantasy landscape\n"
            "```\n\n"

            "**💡 Pro Tips:**\n"
            "• Combine multiple flags: `/flux -l -srealistic -n2`\n"
            "• Use specific seeds to reproduce results\n"
            "• Choose aspect ratios based on usage:\n"
            "  - Social media: `-s` (square)\n"
            "  - Wallpapers: `-l` (landscape)\n"
            "  - Phone screens: `-p` (portrait)\n"
            "  - Cinematic: `-c` (ultra-wide)\n\n"

            f"**⏱️ Rate Limits:**\n"
            f"• {self.config.MAX_REQUESTS_PER_PERIOD} requests per {self.config.RATE_LIMIT_MINUTES} minutes\n\n"

            "✨ *Master the command line for perfect image generation!*"
        )

        await message.reply_text(help_text)

    async def _check_user_permissions(self, message: Message, user_id: int, username: str) -> bool:
        """Check user permissions"""
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
        """Setup enhanced command handlers"""
        @self.app.on_message(filters.command("start"))
        async def start_handler(client, message):
            await self.start_command(client, message)

        @self.app.on_message(filters.command("flux"))
        async def flux_handler(client, message):
            await self.flux_command(client, message)

        @self.app.on_message(filters.command("turbo"))
        async def turbo_handler(client, message):
            await self.turbo_command(client, message)

        @self.app.on_message(filters.command("gptimage"))
        async def gptimage_handler(client, message):
            await self.gptimage_command(client, message)

        @self.app.on_message(filters.command("generate"))
        async def generate_handler(client, message):
            await self.generate_command(client, message)

        @self.app.on_message(filters.command("help"))
        async def help_handler(client, message):
            await self.help_command(client, message)

    async def run(self):
        """Run the bot"""
        try:
            await self.initialize()
            self.setup_handlers()

            await self.bot_logger.log_system_event("MedusaXD Bot started with advanced CLI", "STARTUP")
            logger.info("🚀 MedusaXD Bot starting with advanced command-line interface...")

            async with self.app:
                logger.info("✅ Bot is running with enhanced CLI!")
                await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
        finally:
            await self.bot_logger.close()

async def main():
    """Main entry point"""
    bot = MedusaXDBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
