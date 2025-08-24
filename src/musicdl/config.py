"""Configuration management for MusicDL."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from platformdirs import user_config_dir, user_data_dir
from pydantic import ValidationError

from .core.models import AppConfig

logger = logging.getLogger(__name__)

# Default configuration paths
APP_NAME = "musicdl"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
DATA_DIR = Path(user_data_dir(APP_NAME))
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or CONFIG_FILE
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config

        # Try loading from file
        if self.config_path.exists():
            try:
                config_data = json.loads(self.config_path.read_text())
                self._config = AppConfig(**config_data)
                logger.info(f"Loaded configuration from {self.config_path}")
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Invalid config file {self.config_path}: {e}")
                logger.info("Using default configuration")
                self._config = AppConfig()
        else:
            # Create default config
            self._config = AppConfig()
            logger.info("Using default configuration")

        # Set absolute paths relative to user directories
        self._config = self._resolve_paths(self._config)

        return self._config

    def save(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file."""
        if config is not None:
            self._config = config

        if self._config is None:
            logger.warning("No configuration to save")
            return

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to dict for serialization
            config_dict = self._config.model_dump(mode="json")

            # Convert Path objects to strings
            config_dict = self._serialize_paths(config_dict)

            self.config_path.write_text(json.dumps(config_dict, indent=2))
            logger.info(f"Saved configuration to {self.config_path}")

        except (OSError, IOError) as e:
            logger.error(f"Failed to write config file: {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize config: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving config: {e}")

    def reset(self) -> AppConfig:
        """Reset to default configuration."""
        self._config = AppConfig()
        self._config = self._resolve_paths(self._config)
        return self._config

    def _resolve_paths(self, config: AppConfig) -> AppConfig:
        """Resolve relative paths to absolute user directories."""

        # Create new config with resolved paths
        resolved_data = config.model_dump()

        # Resolve directories relative to user data directory
        if not config.music_dir.is_absolute():
            resolved_data["music_dir"] = DATA_DIR / config.music_dir

        if not config.cache_dir.is_absolute():
            resolved_data["cache_dir"] = DATA_DIR / config.cache_dir

        if not config.logs_dir.is_absolute():
            resolved_data["logs_dir"] = DATA_DIR / config.logs_dir

        return AppConfig(**resolved_data)

    def _serialize_paths(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Path objects to strings for JSON serialization."""

        serialized = {}
        for key, value in config_dict.items():
            if isinstance(value, Path):
                serialized[key] = str(value)
            elif key.endswith("_dir") and isinstance(value, str):
                # These are already strings from model_dump
                serialized[key] = value
            else:
                serialized[key] = value

        return serialized


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration (convenience function)."""
    manager = ConfigManager(config_path)
    return manager.load()


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration (convenience function)."""
    manager = ConfigManager(config_path)
    manager.save(config)


def get_default_config() -> AppConfig:
    """Get default configuration with resolved paths."""
    manager = ConfigManager()
    return manager._resolve_paths(AppConfig())
