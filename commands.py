"""User commands for MedusaXD Bot"""

import asyncio
import re
from datetime import datetime
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import Database
from logger import BotLogger
from config import Config
from infip_provider import MedusaXDImageGenerator
import logging

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, db: Database, bot_logger: BotLogger, config: Config):
        self.db = db
        self.bot_logger = bot_logger
        self.config = config
        self.image_generator = MedusaXDImageGenerator()

    async def _check_user_permissions(self, update: Update, user_id: int, username: str) -> bool:
        """Check if user has permissions to use the bot"""
        # Check if bot is enabled
        bot_status = await self.db.get_bot_status()
        if not bot_status.get('enabled', True):
            await update.message.reply_text(
                "🚫 **MedusaXD Bot is currently disabled.**\n\n"
                "Please try again later.",
                parse_mode='Markdown'
            )
            return False

        # Check if user is authorized
        if not await self.db.is_user_authorized(user_id):
            await update.message.reply_text(
                "🔒 **Access Denied**\n\n"
                "You are not authorized to use MedusaXD Image Generator Bot.\n"
                "Please contact an administrator for access.",
                parse_mode='Markdown'
            )
            return False

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
            return False

        # Update user activity
        await self.db.update_user_activity(user_id, username)
        return True

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        await self.bot_logger.log_user_action(user_id, username, "/help", "Command")

        if not await self._check_user_permissions(update, user_id, username):
            return

        help_text = (
            "🎨 **MedusaXD Image Generator Bot - Help**\n\n"

            "**🖼️ Image Generation Commands:**\n"
            "• `/generate <prompt>` - Generate an image from text\n"
            "• `/models` - View available AI models\n\n"

            "**📊 User Commands:**\n"
            "• `/profile` - View your profile and stats\n"
            "• `/help` - Show this help message\n\n"

            "**🎯 Generation Examples:**\n"
            "• `/generate A majestic dragon flying over mountains`\n"
            "• `/generate A cyberpunk city at night, neon lights`\n"
            "• `/generate Portrait of a wise wizard, fantasy art`\n\n"

            "**⚙️ Advanced Options:**\n"
            "You can specify model and settings:\n"
            "• `/generate [model:img4] [aspect:portrait] Your prompt here`\n\n"

            "**Available Models:**\n"
            f"• `img3` - High-quality general images\n"
            f"• `img4` - Enhanced detail and realism\n"
            f"• `uncen` - Uncensored generation\n\n"

            "**Aspect Ratios:**\n"
            "• `landscape` - 16:9 horizontal\n"
            "• `portrait` - 9:16 vertical\n"
            "• `square` - 1:1 square\n\n"

            f"**⏱️ Rate Limits:**\n"
            f"• Max {self.config.MAX_REQUESTS_PER_PERIOD} requests per {self.config.RATE_LIMIT_MINUTES} minutes\n"
            f"• Max {self.config.MAX_IMAGES_PER_REQUEST} images per request\n\n"

            "**💡 Tips:**\n"
            "• Be descriptive in your prompts\n"
            "• Specify art style, lighting, mood\n"
            "• Use quality keywords like 'detailed', 'high resolution'\n\n"

            "✨ *Unleash your creativity with MedusaXD!*"
        )

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def models_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /models command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        await self.bot_logger.log_user_action(user_id, username, "/models", "Command")

        if not await self._check_user_permissions(update, user_id, username):
            return

        models_text = (
            "🤖 **Available AI Models**\n\n"

            "**🎨 img3** - *Standard Quality*\n"
            "• High-quality general image generation\n"
            "• Fast processing time\n"
            "• Good for most use cases\n\n"

            "**✨ img4** - *Enhanced Quality*\n"
            "• Superior detail and realism\n"
            "• Advanced AI algorithms\n"
            "• Best for professional results\n\n"

            "**🔥 uncen** - *Uncensored*\n"
            "• No content restrictions\n"
            "• Creative freedom\n"
            "• Use responsibly\n\n"

            f"**Default Model:** `{self.config.DEFAULT_MODEL}`\n\n"

            "**How to use:**\n"
            "• Default: `/generate Your amazing prompt`\n"
            "• Specify model: `/generate [model:img4] Your prompt`\n"
            "• With aspect ratio: `/generate [model:img4] [aspect:portrait] Your prompt`\n\n"

            "**💡 Pro Tip:** img4 produces the highest quality but may take slightly longer to generate."
        )

        await update.message.reply_text(models_text, parse_mode='Markdown')

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        await self.bot_logger.log_user_action(user_id, username, "/profile", "Command")

        if not await self._check_user_permissions(update, user_id, username):
            return

        # Get user data
        users = await self.db.get_authorized_users()
        user_data = next((u for u in users if u['user_id'] == user_id), None)

        if not user_data:
            await update.message.reply_text(
                "❌ **Profile not found**\n\nPlease contact an administrator.",
                parse_mode='Markdown'
            )
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
            f"• Member Since: `{user_data.get('authorized_at', 'Unknown').strftime('%Y-%m-%d') if user_data.get('authorized_at') else 'Unknown'}`\n"
            f"• Last Active: `{user_data.get('last_active', 'Unknown').strftime('%Y-%m-%d %H:%M') if user_data.get('last_active') else 'Unknown'}`\n\n"

            f"**⚡ Rate Limit Status:**\n"
            f"• Status: {'✅ Available' if can_generate else '⏳ Limited'}\n"
            f"• Limit: {self.config.MAX_REQUESTS_PER_PERIOD} requests per {self.config.RATE_LIMIT_MINUTES} minutes\n\n"

            f"**🎨 Preferences:**\n"
            f"• Default Model: `{self.config.DEFAULT_MODEL}`\n"
            f"• Max Images: `{self.config.MAX_IMAGES_PER_REQUEST}` per request\n\n"

            "**📈 Want to see more stats?**\n"
            "Contact an admin to view detailed generation history."
        )

        await update.message.reply_text(profile_text, parse_mode='Markdown')

    def _parse_generation_options(self, text: str) -> tuple:
        """Parse generation options from text"""
        model = self.config.DEFAULT_MODEL
        aspect_ratio = "landscape"
        num_images = 1

        # Extract model
        model_match = re.search(r'$$model:(\w+)$$', text, re.IGNORECASE)
        if model_match:
            specified_model = model_match.group(1).lower()
            if specified_model in self.image_generator.get_models():
                model = specified_model
            text = re.sub(r'$$model:\w+$$', '', text, flags=re.IGNORECASE)

        # Extract aspect ratio
        aspect_match = re.search(r'$$aspect:(\w+)$$', text, re.IGNORECASE)
        if aspect_match:
            specified_aspect = aspect_match.group(1).lower()
            if specified_aspect in self.image_generator.get_aspect_ratios():
                aspect_ratio = specified_aspect
            text = re.sub(r'$$aspect:\w+$$', '', text, flags=re.IGNORECASE)

        # Extract number of images
        count_match = re.search(r'$$count:(\d+)$$', text, re.IGNORECASE)
        if count_match:
            specified_count = int(count_match.group(1))
            if 1 <= specified_count <= self.config.MAX_IMAGES_PER_REQUEST:
                num_images = specified_count
            text = re.sub(r'$$count:\d+$$', '', text, flags=re.IGNORECASE)

        # Clean up the prompt
        prompt = text.strip()

        return prompt, model, aspect_ratio, num_images

    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /generate command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        await self.bot_logger.log_user_action(user_id, username, "/generate", "Command")

        if not await self._check_user_permissions(update, user_id, username):
            return

        # Check rate limit
        if not await self.db.check_rate_limit(user_id, self.config.RATE_LIMIT_MINUTES, self.config.MAX_REQUESTS_PER_PERIOD):
            await update.message.reply_text(
                f"⏳ **Rate limit exceeded**\n\n"
                f"You can make {self.config.MAX_REQUESTS_PER_PERIOD} requests every {self.config.RATE_LIMIT_MINUTES} minutes.\n"
                "Please wait before making another request.",
                parse_mode='Markdown'
            )
            return

        # Get prompt from command
        if not context.args:
            await update.message.reply_text(
                "❌ **No prompt provided**\n\n"
                "**Usage:** `/generate Your amazing prompt here`\n\n"
                "**Examples:**\n"
                "• `/generate A majestic dragon in a fantasy landscape`\n"
                "• `/generate [model:img4] Cyberpunk cityscape at night`\n"
                "• `/generate [aspect:portrait] Portrait of a wise wizard`\n\n"
                "Use `/help` for more detailed instructions.",
                parse_mode='Markdown'
            )
            return

        prompt_text = " ".join(context.args)

        # Parse options
        prompt, model, aspect_ratio, num_images = self._parse_generation_options(prompt_text)

        if len(prompt.strip()) < 3:
            await update.message.reply_text(
                "❌ **Prompt too short**\n\n"
                "Please provide a more descriptive prompt (at least 3 characters).",
                parse_mode='Markdown'
            )
            return

        # Record the request for rate limiting
        await self.db.record_request(user_id)

        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🎨 **Generating {num_images} image(s)...**\n\n"
            f"**Model:** `{model}`\n"
            f"**Aspect Ratio:** `{aspect_ratio}`\n"
            f"**Prompt:** {prompt}\n\n"
            "⏳ *This may take a few moments...*",
            parse_mode='Markdown'
        )

        try:
            # Generate images
            response = await self.image_generator.generate_images(
                prompt=prompt,
                model=model,
                num_images=num_images,
                aspect_ratio=aspect_ratio
            )

            # Delete processing message
            try:
                await processing_msg.delete()
            except:
                pass

            # Send generated images
            image_urls = [img.url for img in response.data]

            # Send images
            for i, image_url in enumerate(image_urls):
                caption = (
                    f"🎨 **MedusaXD Generated Image {i+1}/{len(image_urls)}**\n\n"
                    f"**Prompt:** {prompt}\n"
                    f"**Model:** `{model}` | **Aspect:** `{aspect_ratio}`\n"
                    f"**Generated by:** @{username} (`{user_id}`)"
                )

                try:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send image {i+1}: {e}")
                    await update.message.reply_text(
                        f"❌ **Failed to send image {i+1}**\n\n"
                        f"Image URL: {image_url}",
                        parse_mode='Markdown'
                    )

            # Update user statistics
            await self.db.increment_user_generations(user_id)

            # Log the generation
            await self.db.log_generation(
                user_id=user_id,
                username=username,
                prompt=prompt,
                model=model,
                images=image_urls,
                success=True
            )

            # Log to admin channel
            await self.bot_logger.log_image_generation(
                user_id, username, prompt, model, aspect_ratio, image_urls
            )

        except Exception as e:
            logger.error(f"Image generation failed for user {user_id}: {e}")

            # Delete processing message
            try:
                await processing_msg.delete()
            except:
                pass

            # Send error message
            await update.message.reply_text(
                f"❌ **Image generation failed**\n\n"
                f"**Error:** {str(e)}\n\n"
                "Please try again with a different prompt or contact an administrator if the issue persists.",
                parse_mode='Markdown'
            )

            # Log the failure
            await self.db.log_generation(
                user_id=user_id,
                username=username,
                prompt=prompt,
                model=model,
                images=[],
                success=False,
                error=str(e)
            )
