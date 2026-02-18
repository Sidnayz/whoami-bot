"""Configuration module."""

import os
from typing import Optional


class BotConfig:
    """Bot configuration."""

    BOT_TOKEN: str
    DEBUG: bool = False

    @classmethod
    def load(cls) -> None:
        """Load configuration from environment variables."""
        cls.BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        cls.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        return bool(cls.BOT_TOKEN)


# Load configuration on import
BotConfig.load()
