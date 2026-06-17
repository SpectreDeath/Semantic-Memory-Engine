"""
Centralized Configuration Management

This module provides a singleton configuration class that loads and manages
all SimpleMem Laboratory settings from config/config.yaml.

Usage:
    from src.core.config import Config

    config = Config()
    db_path = config.get('storage.db_path')
    # or with defaults:
    timeout = config.get('mcp.timeout', default=30)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "storage": {
        "base_dir": "./data",
        "db_path": "./data/storage/laboratory.db",
        "log_dir": "./data/logs",
        "lexicon_dir": "./data/lexicons",
    },
    "analysis": {
        "thresholds": {
            "high_alert_sentiment": 0.4,
            "similarity_threshold": 0.6,
        },
        "lookback_days": 7,
    },
    "mcp": {
        "host": "localhost",
        "port": 8000,
    },
    "nltk": {
        "data_dir": "./data/nltk_data",
        "auto_download": True,
        "install_optional": False,
        "languages": ["english"],
    },
    "hardware": {
        "vram_limit_mb": 6144,
        "offload_threshold_mb": 5500,
        "offload_strategy": "gguf_first",
        "lora_dir": "models/adapters",
        "gguf_dir": "models/gguf",
        "base_model": "models/gguf/mistral-7b-v0.1.Q4_K_M.gguf",
    },
    "skills": {
        "enabled": True,
        "directory": "./skills",
        "registry_path": "./skills/registry.json",
        "auto_rebuild": False,
    },
}


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class Config:
    """
    Singleton configuration manager for SimpleMem Laboratory.

    Loads configuration from config/config.yaml and provides typed access
    to settings with sensible defaults.
    """

    _instance: Config | None = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        cls._instance = None
        cls._config = {}

    def _load_config(self) -> None:
        """Load configuration from config.yaml."""
        config_path = self._find_config_file()

        if not config_path:
            self._config = DEFAULT_CONFIG.copy()
            return

        try:
            with open(config_path) as f:
                loaded = yaml.safe_load(f) or {}
            self._config = self._deep_merge(DEFAULT_CONFIG, loaded)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {config_path}: {e}")

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _find_config_file() -> Path | None:
        """Find config.yaml in various possible locations."""
        project_root = Path(__file__).resolve().parents[2]
        possible_paths = [
            Path("config/config.yaml"),
            Path("./config/config.yaml"),
            project_root / "config" / "config.yaml",
        ]

        for path in possible_paths:
            if path.resolve().exists():
                return path.resolve()

        return None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'storage.db_path')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            db_path = config.get('storage.db_path')
            timeout = config.get('mcp.timeout', default=30)
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise ConfigError(f"Configuration key '{key}' not found")

    def get_safe(self, key: str, default: Any = None) -> Any:
        """
        Safely get a configuration value, always returning default if not found.

        Args:
            key: Configuration key in dot notation
            default: Default value if key not found

        Returns:
            Configuration value or default (never raises)
        """
        try:
            return self.get(key, default)
        except ConfigError:
            return default

    def get_path(self, key: str, default: str | None = None) -> Path:
        """
        Get a configuration path value and return as Path object.

        Automatically expands environment variables and handles Windows paths.

        Args:
            key: Configuration key in dot notation
            default: Default path if key not found

        Returns:
            pathlib.Path object
        """
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Path configuration key '{key}' not found")

        # Expand environment variables and convert to Path
        expanded = os.path.expandvars(str(value))
        path = Path(expanded)

        return path

    def get_int(self, key: str, default: int | None = None) -> int:
        """Get an integer configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        return int(value)

    def get_float(self, key: str, default: float | None = None) -> float:
        """Get a float configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        return float(value)

    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """Get a boolean configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        return bool(value)

    def get_list(self, key: str, default: list | None = None) -> list:
        """Get a list configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        if not isinstance(value, list):
            return [value]
        return value

    def all(self) -> dict[str, Any]:
        """Return entire configuration dictionary."""
        return self._config.copy()

    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = {}
        self._load_config()

    def __repr__(self) -> str:
        return f"Config(paths={len(self._config)} sections)"


# Convenience singleton instance
_config_instance = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return _config_instance
