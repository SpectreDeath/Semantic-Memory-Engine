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

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """
    Singleton configuration manager for SimpleMem Laboratory.
    
    Loads configuration from config/config.yaml and provides typed access
    to settings with sensible defaults.
    """
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
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
            raise ConfigError(
                "config.yaml not found. Expected at: config/config.yaml"
            )
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Failed to load config from {config_path}: {e}")
    
    @staticmethod
    def _find_config_file() -> Optional[Path]:
        """Find config.yaml in various possible locations."""
        possible_paths = [
            Path("config/config.yaml"),
            Path("./config/config.yaml"),
            Path(__file__).parent.parent.parent / "config" / "config.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
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
        keys = key.split('.')
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
    
    def get_path(self, key: str, default: Optional[str] = None) -> Path:
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
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get an integer configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        return int(value)
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get a float configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        return float(value)
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """Get a boolean configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        return bool(value)
    
    def get_list(self, key: str, default: Optional[list] = None) -> list:
        """Get a list configuration value."""
        value = self.get(key, default)
        if value is None:
            raise ConfigError(f"Configuration key '{key}' not found")
        if not isinstance(value, list):
            return [value]
        return value
    
    def all(self) -> Dict[str, Any]:
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
