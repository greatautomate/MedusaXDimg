"""Utility functions for MedusaXD Bot"""

import re
import html
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def validate_user_id(user_id_str: str) -> Optional[int]:
    """Validate and convert user ID string to integer"""
    try:
        user_id = int(user_id_str)
        if user_id > 0:
            return user_id
    except ValueError:
        pass
    return None

def format_user_info(user_data: Dict[str, Any]) -> str:
    """Format user information for display"""
    username = user_data.get('username', 'Unknown')
    user_id = user_data.get('user_id', 'Unknown')
    generations = user_data.get('total_generations', 0)

    last_active = user_data.get('last_active')
    if isinstance(last_active, datetime):
        last_active_str = last_active.strftime('%Y-%m-%d %H:%M')
    else:
        last_active_str = 'Never'

    return f"@{username} ({user_id}) - {generations} gen, active: {last_active_str}"

def parse_time_period(period_str: str) -> Optional[timedelta]:
    """Parse time period string like '1h', '30m', '7d'"""
    pattern = r'^(\d+)([hdm])$'
    match = re.match(pattern, period_str.lower())

    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)

    return None

def format_stats(stats: Dict[str, Any]) -> str:
    """Format statistics for display"""
    return (
        f"Users: {stats.get('total_users', 0)} | "
        f"Banned: {stats.get('total_banned', 0)} | "
        f"Generations: {stats.get('total_generations', 0)} | "
        f"Recent: {stats.get('recent_generations_24h', 0)}"
    )

def clean_prompt(prompt: str) -> str:
    """Clean and validate prompt text"""
    # Remove extra whitespace
    prompt = re.sub(r'\s+', ' ', prompt.strip())

    # Remove HTML tags
    prompt = html.unescape(prompt)
    prompt = re.sub(r'<[^>]+>', '', prompt)

    # Limit length
    if len(prompt) > 1000:
        prompt = prompt[:1000]

    return prompt

def is_valid_aspect_ratio(aspect_ratio: str) -> bool:
    """Check if aspect ratio is valid"""
    valid_ratios = ['landscape', 'portrait', 'square']
    return aspect_ratio.lower() in valid_ratios

def is_valid_model(model: str) -> bool:
    """Check if model is valid"""
    valid_models = ['img3', 'img4', 'uncen']
    return model.lower() in valid_models

def format_error_message(error: Exception, user_friendly: bool = True) -> str:
    """Format error message for display"""
    if user_friendly:
        error_mapping = {
            'ConnectionError': 'Connection failed. Please try again later.',
            'TimeoutError': 'Request timed out. Please try again.',
            'ValueError': 'Invalid input provided.',
            'RuntimeError': 'Service temporarily unavailable.',
        }

        error_type = type(error).__name__
        return error_mapping.get(error_type, 'An unexpected error occurred.')
    else:
        return str(error)

def get_file_size_mb(size_bytes: int) -> float:
    """Convert bytes to megabytes"""
    return round(size_bytes / (1024 * 1024), 2)

def is_image_url(url: str) -> bool:
    """Check if URL appears to be an image"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    return any(url.lower().endswith(ext) for ext in image_extensions)

def generate_user_report(user_data: Dict[str, Any]) -> str:
    """Generate detailed user report"""
    username = user_data.get('username', 'Unknown')
    user_id = user_data.get('user_id', 'Unknown')
    generations = user_data.get('total_generations', 0)
    authorized_at = user_data.get('authorized_at')
    last_active = user_data.get('last_active')

    report = f"📊 **User Report: @{username}**\n\n"
    report += f"**User ID:** `{user_id}`\n"
    report += f"**Total Generations:** {generations}\n"

    if authorized_at:
        if isinstance(authorized_at, datetime):
            report += f"**Member Since:** {authorized_at.strftime('%Y-%m-%d')}\n"

    if last_active:
        if isinstance(last_active, datetime):
            report += f"**Last Active:** {last_active.strftime('%Y-%m-%d %H:%M')}\n"

    return report
