"""Configuration management for Safety Research System."""
import os
from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    """Configuration loader and manager."""

    def __init__(self, environment: str = None):
        """
        Initialize configuration.

        Args:
            environment: Environment name (development, staging, production)
                        If not provided, uses APP_ENV or ENVIRONMENT env var
        """
        self.environment = environment or os.getenv("APP_ENV") or os.getenv("ENVIRONMENT", "development")
        self.config_dir = Path(__file__).parent
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML files."""
        # Load base configuration
        base_config_path = self.config_dir / "base.yaml"
        if base_config_path.exists():
            with open(base_config_path, "r") as f:
                base_config = yaml.safe_load(f)
                self._config = base_config or {}

        # Load environment-specific configuration
        env_config_path = self.config_dir / f"{self.environment}.yaml"
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    self._deep_merge(self._config, env_config)

        # Substitute environment variables
        self._substitute_env_vars(self._config)

    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _substitute_env_vars(self, config: Dict):
        """Recursively substitute ${VAR_NAME} with environment variables."""
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, value)
            elif isinstance(value, dict):
                self._substitute_env_vars(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                        env_var = item[2:-1]
                        value[i] = os.getenv(env_var, item)
                    elif isinstance(item, dict):
                        self._substitute_env_vars(item)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "database.pool_size")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.

        Args:
            section: Section name (e.g., "database")

        Returns:
            Configuration section as dict
        """
        return self.get(section, {})

    @property
    def all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self._config.copy()

    def validate(self) -> bool:
        """
        Validate required configuration values.

        Returns:
            True if valid, raises ValueError if not
        """
        required_keys = [
            "database.url",
            "redis.url",
            "security.jwt_algorithm",
        ]

        missing = []
        for key in required_keys:
            value = self.get(key)
            if value is None or (isinstance(value, str) and value.startswith("${")):
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required configuration values: {', '.join(missing)}")

        return True


# Global configuration instance
_config = None


def get_config(environment: str = None) -> Config:
    """
    Get global configuration instance.

    Args:
        environment: Environment name (optional)

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(environment)
    return _config


def reload_config(environment: str = None):
    """
    Reload configuration.

    Args:
        environment: Environment name (optional)
    """
    global _config
    _config = Config(environment)
    return _config
