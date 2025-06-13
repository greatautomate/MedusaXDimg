"""Admin commands and panel for MedusaXD Bot"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from datetime import datetime
from typing import List

from database import Database
from logger import BotLogger
from config import Config
import logging

logger = logging.getLogger(__name__)

class AdminHandler:
    def __init__(self, db: Database, bot_logger: BotLogger, config: Config):
        self.db = db
        self.bot_logger = bot_logger
        self.config = config

    async def _check_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return await self.db.is_admin(user_id)

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel with buttons"""
        user_id = update.effective_user.id

        if not await self._check_admin(user_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        # Get statistics
        stats = await self.db.get_stats()
        bot_status = await self.db.get_bot_status()

        # Create admin panel message
        panel_text = (
            "🔧 **MedusaXD Admin Panel**\n\n"

            f"**📊 Bot Statistics:**\n"
            f"• Status: {'✅ Enabled' if bot_status.get('enabled', True) else '🔴 Disabled'}\n"
            f"• Total Users: `{stats.get('total_users', 0)}`\n"
            f"• Banned Users: `{stats.get('total_banned', 0)}`\n"
            f"• Total Generations: `{stats.get('total_generations', 0)}`\n"
            f"• Recent (24h): `{stats.get('recent_generations_24h', 0)}`\n"
            f"• Active Users (7d): `{stats.get('active_users_7d', 0)}`\n\n"

            "**🎛️ Use the buttons below to manage the bot:**"
        )

        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("👥 Manage Users", callback_data="admin_users"),
                InlineKeyboardButton("🚫 Manage Bans", callback_data="admin_bans")
            ],
            [
                InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_stats"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(
                    "🔴 Disable Bot" if bot_status.get('enabled', True) else "✅ Enable Bot",
                    callback_data="admin_toggle_bot"
                ),
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            panel_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel button callbacks"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin(user_id):
            await query.answer("❌ Access Denied", show_alert=True)
            return

        await query.answer()

        if query.data == "admin_refresh":
            # Refresh the admin panel
            await self._refresh_admin_panel(query)
        elif query.data == "admin_users":
            await self._show_users_management(query)
        elif query.data == "admin_bans":
            await self._show_bans_management(query)
        elif query.data == "admin_stats":
            await self._show_detailed_stats(query)
        elif query.data == "admin_broadcast":
            await self._show_broadcast_info(query)
        elif query.data == "admin_toggle_bot":
            await self._toggle_bot_status(query)

    async def _refresh_admin_panel(self, query):
        """Refresh the admin panel"""
        stats = await self.db.get_stats()
        bot_status = await self.db.get_bot_status()

        panel_text = (
            "🔧 **MedusaXD Admin Panel**\n\n"

            f"**📊 Bot Statistics:**\n"
            f"• Status: {'✅ Enabled' if bot_status.get('enabled', True) else '🔴 Disabled'}\n"
            f"• Total Users: `{stats.get('total_users', 0)}`\n"
            f"• Banned Users: `{stats.get('total_banned', 0)}`\n"
            f"• Total Generations: `{stats.get('total_generations', 0)}`\n"
            f"• Recent (24h): `{stats.get('recent_generations_24h', 0)}`\n"
            f"• Active Users (7d): `{stats.get('active_users_7d', 0)}`\n\n"

            "**🎛️ Use the buttons below to manage the bot:**"
        )

        keyboard = [
            [
                InlineKeyboardButton("👥 Manage Users", callback_data="admin_users"),
                InlineKeyboardButton("🚫 Manage Bans", callback_data="admin_bans")
            ],
            [
                InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_stats"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(
                    "🔴 Disable Bot" if bot_status.get('enabled', True) else "✅ Enable Bot",
                    callback_data="admin_toggle_bot"
                ),
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            panel_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _show_users_management(self, query):
        """Show users management interface"""
        users = await self.db.get_authorized_users()

        if not users:
            text = "👥 **User Management**\n\n❌ No authorized users found."
        else:
            text = f"👥 **User Management** ({len(users)} users)\n\n"

            for user in users[:10]:  # Show first 10 users
                username = user.get('username', 'Unknown')
                user_id = user['user_id']
                generations = user.get('total_generations', 0)
                last_active = user.get('last_active', 'Never')

                if isinstance(last_active, datetime):
                    last_active = last_active.strftime('%Y-%m-%d')

                text += f"• @{username} (`{user_id}`)\n"
                text += f"  Generations: {generations} | Active: {last_active}\n\n"

            if len(users) > 10:
                text += f"... and {len(users) - 10} more users\n\n"

            text += (
                "**Commands:**\n"
                "• `/users` - List all users\n"
                "• `/adduser <user_id>` - Add user\n"
                "• `/removeuser <user_id>` - Remove user"
            )

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _show_bans_management(self, query):
        """Show bans management interface"""
        banned_users = await self.db.get_banned_users()

        if not banned_users:
            text = "🚫 **Ban Management**\n\n✅ No banned users."
        else:
            text = f"🚫 **Ban Management** ({len(banned_users)} banned)\n\n"

            for ban in banned_users[:10]:  # Show first 10 bans
                user_id = ban['user_id']
                reason = ban.get('reason', 'No reason')
                banned_at = ban.get('banned_at', 'Unknown')

                if isinstance(banned_at, datetime):
                    banned_at = banned_at.strftime('%Y-%m-%d')

                text += f"• User `{user_id}`\n"
                text += f"  Reason: {reason}\n"
                text += f"  Banned: {banned_at}\n\n"

            if len(banned_users) > 10:
                text += f"... and {len(banned_users) - 10} more bans\n\n"

            text += (
                "**Commands:**\n"
                "• `/ban <user_id> [reason]` - Ban user\n"
                "• `/unban <user_id>` - Unban user"
            )

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _show_detailed_stats(self, query):
        """Show detailed statistics"""
        stats = await self.db.get_stats()

        text = (
            "📊 **Detailed Statistics**\n\n"

            f"**👥 Users:**\n"
            f"• Total Authorized: `{stats.get('total_users', 0)}`\n"
            f"• Active (7 days): `{stats.get('active_users_7d', 0)}`\n"
            f"• Banned: `{stats.get('total_banned', 0)}`\n\n"

            f"**🎨 Generations:**\n"
            f"• Total: `{stats.get('total_generations', 0)}`\n"
            f"• Last 24 hours: `{stats.get('recent_generations_24h', 0)}`\n\n"

            f"**⚙️ Configuration:**\n"
            f"• Max requests per period: `{self.config.MAX_REQUESTS_PER_PERIOD}`\n"
            f"• Rate limit period: `{self.config.RATE_LIMIT_MINUTES}` minutes\n"
            f"• Max images per request: `{self.config.MAX_IMAGES_PER_REQUEST}`\n"
            f"• Default model: `{self.config.DEFAULT_MODEL}`\n\n"

            f"**📅 Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _show_broadcast_info(self, query):
        """Show broadcast information"""
        text = (
            "📢 **Broadcast Messages**\n\n"

            "**How to broadcast:**\n"
            "• `/broadcast <message>` - Send to all users\n\n"

            "**Features:**\n"
            "• Supports Markdown formatting\n"
            "• Sends to all authorized users\n"
            "• Shows delivery statistics\n\n"

            "**Example:**\n"
            "`/broadcast 🎉 **Update Alert**\\n\\nNew features available!`\n\n"

            "⚠️ **Note:** Use broadcasts responsibly to avoid spam."
        )

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _toggle_bot_status(self, query):
        """Toggle bot enabled/disabled status"""
        current_status = await self.db.get_bot_status()
        new_status = not current_status.get('enabled', True)

        success = await self.db.set_bot_status(new_status)

        if success:
            status_text = "enabled" if new_status else "disabled"
            await query.edit_message_text(
                f"✅ **Bot {status_text} successfully**\n\n"
                f"Bot is now {'✅ Enabled' if new_status else '🔴 Disabled'}.\n\n"
                "Click refresh to update the admin panel.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
                ]])
            )

            # Log admin action
            await self.db.log_admin_action(
                query.from_user.id,
                f"Bot {'enabled' if new_status else 'disabled'}",
                details=f"Bot status changed to {status_text}"
            )
        else:
            await query.edit_message_text(
                "❌ **Failed to change bot status**\n\n"
                "Please try again.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
                ]])
            )

    # Command handlers
    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add user to authorized list"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "❌ **Invalid usage**\n\n"
                "**Usage:** `/adduser <user_id>`\n"
                "**Example:** `/adduser 123456789`"
            )
            return

        user_id = int(context.args[0])
        username = context.args[1] if len(context.args) > 1 else None

        # Check if user is already authorized
        if await self.db.is_user_authorized(user_id):
            await update.message.reply_text(
                f"ℹ️ **User already authorized**\n\n"
                f"User `{user_id}` is already in the authorized list."
            )
            return

        success = await self.db.add_authorized_user(user_id, username, admin_id)

        if success:
            await update.message.reply_text(
                f"✅ **User added successfully**\n\n"
                f"User `{user_id}` has been added to the authorized list."
            )

            # Log admin action
            await self.db.log_admin_action(
                admin_id,
                "User added",
                target_user=user_id,
                details=f"Added user {user_id} to authorized list"
            )

            # Log to admin channel
            await self.bot_logger.log_admin_action(
                admin_id, f"Added user {user_id} to authorized list"
            )
        else:
            await update.message.reply_text(
                f"❌ **Failed to add user**\n\n"
                f"Could not add user `{user_id}` to the authorized list."
            )

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove user from authorized list"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "❌ **Invalid usage**\n\n"
                "**Usage:** `/removeuser <user_id>`\n"
                "**Example:** `/removeuser 123456789`"
            )
            return

        user_id = int(context.args[0])

        # Check if user is authorized
        if not await self.db.is_user_authorized(user_id):
            await update.message.reply_text(
                f"ℹ️ **User not found**\n\n"
                f"User `{user_id}` is not in the authorized list."
            )
            return

        success = await self.db.remove_authorized_user(user_id)

        if success:
            await update.message.reply_text(
                f"✅ **User removed successfully**\n\n"
                f"User `{user_id}` has been removed from the authorized list."
            )

            # Log admin action
            await self.db.log_admin_action(
                admin_id,
                "User removed",
                target_user=user_id,
                details=f"Removed user {user_id} from authorized list"
            )

            # Log to admin channel
            await self.bot_logger.log_admin_action(
                admin_id, f"Removed user {user_id} from authorized list"
            )
        else:
            await update.message.reply_text(
                f"❌ **Failed to remove user**\n\n"
                f"Could not remove user `{user_id}` from the authorized list."
            )

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "❌ **Invalid usage**\n\n"
                "**Usage:** `/ban <user_id> [reason]`\n"
                "**Example:** `/ban 123456789 Spam behavior`"
            )
            return

        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"

        # Check if user is already banned
        if await self.db.is_user_banned(user_id):
            await update.message.reply_text(
                f"ℹ️ **User already banned**\n\n"
                f"User `{user_id}` is already banned."
            )
            return

        success = await self.db.ban_user(user_id, reason, admin_id)

        if success:
            await update.message.reply_text(
                f"✅ **User banned successfully**\n\n"
                f"**User:** `{user_id}`\n"
                f"**Reason:** {reason}\n"
                f"**Banned by:** Admin `{admin_id}`"
            )

            # Log admin action
            await self.db.log_admin_action(
                admin_id,
                "User banned",
                target_user=user_id,
                details=f"Banned user {user_id}: {reason}"
            )

            # Log to admin channel
            await self.bot_logger.log_admin_action(
                admin_id, f"Banned user {user_id}: {reason}"
            )
        else:
            await update.message.reply_text(
                f"❌ **Failed to ban user**\n\n"
                f"Could not ban user `{user_id}`."
            )

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text(
                "❌ **Invalid usage**\n\n"
                "**Usage:** `/unban <user_id>`\n"
                "**Example:** `/unban 123456789`"
            )
            return

        user_id = int(context.args[0])

        # Check if user is banned
        if not await self.db.is_user_banned(user_id):
            await update.message.reply_text(
                f"ℹ️ **User not banned**\n\n"
                f"User `{user_id}` is not currently banned."
            )
            return

        success = await self.db.unban_user(user_id)

        if success:
            await update.message.reply_text(
                f"✅ **User unbanned successfully**\n\n"
                f"User `{user_id}` has been unbanned."
            )

            # Log admin action
            await self.db.log_admin_action(
                admin_id,
                "User unbanned",
                target_user=user_id,
                details=f"Unbanned user {user_id}"
            )

            # Log to admin channel
            await self.bot_logger.log_admin_action(
                admin_id, f"Unbanned user {user_id}"
            )
        else:
            await update.message.reply_text(
                f"❌ **Failed to unban user**\n\n"
                f"Could not unban user `{user_id}`."
            )

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ **No message provided**\n\n"
                "**Usage:** `/broadcast <message>`\n"
                "**Example:** `/broadcast 🎉 **Update Alert**\\n\\nNew features available!`\n\n"
                "**Note:** Use \\\\n for line breaks in the message."
            )
            return

        message = " ".join(context.args).replace("\\n", "\n")

        # Get all authorized users
        users = await self.db.get_authorized_users()

        if not users:
            await update.message.reply_text("❌ **No users to broadcast to**")
            return

        # Send confirmation
        confirm_msg = await update.message.reply_text(
            f"📢 **Broadcasting to {len(users)} users...**\n\n"
            "⏳ *This may take a few moments...*"
        )

        # Broadcast to users
        success_count = 0
        fail_count = 0

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 **Broadcast Message**\n\n{message}",
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
                fail_count += 1

        # Update confirmation message
        await confirm_msg.edit_text(
            f"📢 **Broadcast Complete**\n\n"
            f"✅ **Delivered:** {success_count} users\n"
            f"❌ **Failed:** {fail_count} users\n"
            f"📊 **Total:** {len(users)} users\n\n"
            f"**Message:** {message[:100]}{'...' if len(message) > 100 else ''}",
            parse_mode='Markdown'
        )

        # Log admin action
        await self.db.log_admin_action(
            admin_id,
            "Broadcast sent",
            details=f"Sent to {success_count}/{len(users)} users: {message[:50]}..."
        )

        # Log to admin channel
        await self.bot_logger.log_admin_action(
            admin_id, f"Broadcast sent to {success_count}/{len(users)} users"
        )

    async def list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all authorized users"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        users = await self.db.get_authorized_users()

        if not users:
            await update.message.reply_text("❌ **No authorized users found**")
            return

        # Sort users by total generations
        users.sort(key=lambda x: x.get('total_generations', 0), reverse=True)

        message_parts = []
        current_message = f"👥 **Authorized Users** ({len(users)} total)\n\n"

        for i, user in enumerate(users, 1):
            username = user.get('username', 'Unknown')
            user_id = user['user_id']
            generations = user.get('total_generations', 0)
            last_active = user.get('last_active', 'Never')

            if isinstance(last_active, datetime):
                last_active = last_active.strftime('%m-%d')

            user_line = f"{i}. @{username} (`{user_id}`)\n"
            user_line += f"   Gen: {generations} | Active: {last_active}\n\n"

            # Check if adding this user would exceed message length limit
            if len(current_message + user_line) > 4000:
                message_parts.append(current_message)
                current_message = f"👥 **Authorized Users** (continued)\n\n{user_line}"
            else:
                current_message += user_line

        # Add the last part
        if current_message.strip():
            message_parts.append(current_message)

        # Send all message parts
        for part in message_parts:
            await update.message.reply_text(part, parse_mode='Markdown')

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed bot statistics"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        stats = await self.db.get_stats()
        bot_status = await self.db.get_bot_status()

        stats_text = (
            "📊 **MedusaXD Bot Statistics**\n\n"

            f"**🤖 Bot Status:**\n"
            f"• Status: {'✅ Enabled' if bot_status.get('enabled', True) else '🔴 Disabled'}\n"
            f"• Uptime: Since last restart\n\n"

            f"**👥 User Statistics:**\n"
            f"• Total Authorized: `{stats.get('total_users', 0)}`\n"
            f"• Active (7 days): `{stats.get('active_users_7d', 0)}`\n"
            f"• Banned Users: `{stats.get('total_banned', 0)}`\n\n"

            f"**🎨 Generation Statistics:**\n"
            f"• Total Generations: `{stats.get('total_generations', 0)}`\n"
            f"• Last 24 Hours: `{stats.get('recent_generations_24h', 0)}`\n\n"

            f"**⚙️ Configuration:**\n"
            f"• Rate Limit: {self.config.MAX_REQUESTS_PER_PERIOD} req/{self.config.RATE_LIMIT_MINUTES}min\n"
            f"• Max Images: {self.config.MAX_IMAGES_PER_REQUEST} per request\n"
            f"• Default Model: {self.config.DEFAULT_MODEL}\n\n"

            f"**📅 Report Generated:**\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def bot_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle bot status or show current status"""
        admin_id = update.effective_user.id

        if not await self._check_admin(admin_id):
            await update.message.reply_text("❌ **Access Denied** - Admin only command.")
            return

        if context.args and context.args[0].lower() in ['enable', 'disable', 'on', 'off']:
            # Toggle bot status
            new_status = context.args[0].lower() in ['enable', 'on']
            success = await self.db.set_bot_status(new_status)

            if success:
                status_text = "enabled" if new_status else "disabled"
                await update.message.reply_text(
                    f"✅ **Bot {status_text} successfully**\n\n"
                    f"Bot is now {'✅ Enabled' if new_status else '🔴 Disabled'}."
                )

                # Log admin action
                await self.db.log_admin_action(
                    admin_id,
                    f"Bot {status_text}",
                    details=f"Bot status changed to {status_text}"
                )
            else:
                await update.message.reply_text("❌ **Failed to change bot status**")
        else:
            # Show current status
            bot_status = await self.db.get_bot_status()
            status_emoji = "✅" if bot_status.get('enabled', True) else "🔴"
            status_text = "Enabled" if bot_status.get('enabled', True) else "Disabled"

            await update.message.reply_text(
                f"🤖 **Bot Status:** {status_emoji} {status_text}\n\n"
                f"**Usage:**\n"
                f"• `/botstatus enable` - Enable the bot\n"
                f"• `/botstatus disable` - Disable the bot\n"
                f"• `/botstatus` - Show current status"
            )
