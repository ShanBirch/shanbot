"""
Configuration Utilities
=======================
Configuration management for the Shanbot webhook system.
"""

import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("shanbot_config")


class Config:
    """Configuration manager for the webhook system."""

    # API Keys
    MANYCHAT_API_KEY: Optional[str] = os.getenv("MANYCHAT_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    INSTAGRAM_GRAPH_API_TOKEN: Optional[str] = os.getenv(
        "INSTAGRAM_GRAPH_API_TOKEN")
    TRAINERIZE_USERNAME: Optional[str] = os.getenv("TRAINERIZE_USERNAME")
    TRAINERIZE_PASSWORD: Optional[str] = os.getenv("TRAINERIZE_PASSWORD")

    # Application Settings
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Message Buffer Settings
    BUFFER_WINDOW: float = float(os.getenv("BUFFER_WINDOW", "8.0"))
    DEFAULT_USE_BUFFERING: bool = os.getenv(
        "DEFAULT_USE_BUFFERING", "true").lower() == "true"

    # Database Settings
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", "app/database/manychat_data.db")

    @classmethod
    def validate_required_keys(cls) -> Dict[str, bool]:
        """Validate that required API keys are present."""
        required_keys = {
            "MANYCHAT_API_KEY": bool(cls.MANYCHAT_API_KEY),
            "GEMINI_API_KEY": bool(cls.GEMINI_API_KEY),
            "INSTAGRAM_GRAPH_API_TOKEN": bool(cls.INSTAGRAM_GRAPH_API_TOKEN),
        }

        missing_keys = [key for key,
                        present in required_keys.items() if not present]

        if missing_keys:
            logger.warning(f"Missing required API keys: {missing_keys}")
        else:
            logger.info("All required API keys are present")

        return required_keys

    @classmethod
    def get_api_status(cls) -> Dict[str, Any]:
        """Get status of all API configurations."""
        return {
            "api_keys": cls.validate_required_keys(),
            "app_config": {
                "host": cls.APP_HOST,
                "port": cls.APP_PORT,
                "debug": cls.DEBUG,
                "log_level": cls.LOG_LEVEL
            },
            "buffer_config": {
                "buffer_window": cls.BUFFER_WINDOW,
                "default_use_buffering": cls.DEFAULT_USE_BUFFERING
            }
        }
