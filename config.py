"""Configuration management for MedusaXD Bot"""

import os
from typing import List

class Config:
    """Bot configuration from environment variables"""

    def __init__(self):
        # Required environment variables
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.MONGODB_URL = os.getenv("MONGODB_URL")
        self.LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

        # Admin user IDs (comma-separated)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip().isdigit()]

        # Optional settings with defaults
        self.MAX_IMAGES_PER_REQUEST = int(os.getenv("MAX_IMAGES_PER_REQUEST", "4"))
        self.RATE_LIMIT_MINUTES = int(os.getenv("RATE_LIMIT_MINUTES", "5"))
        self.MAX_REQUESTS_PER_PERIOD = int(os.getenv("MAX_REQUESTS_PER_PERIOD", "10"))
        self.DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "img3")
        self.DEFAULT_ASPECT_RATIO = os.getenv("DEFAULT_ASPECT_RATIO", "IMAGE_ASPECT_RATIO_LANDSCAPE")

        # Validate required settings
        self._validate_config()

    def _validate_config(self):
        """Validate required configuration"""
        required_vars = {
            "BOT_TOKEN": self.BOT_TOKEN,
            "MONGODB_URL": self.MONGODB_URL,
            "LOG_CHANNEL_ID": self.LOG_CHANNEL_ID,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        if not self.ADMIN_IDS:
            raise ValueError("At least one admin ID must be specified in ADMIN_IDS environment variable")

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return os.getenv("RENDER") == "true"  # Render sets this automatically
