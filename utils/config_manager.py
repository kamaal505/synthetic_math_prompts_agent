"""
Centralized configuration management system.

This module provides a singleton ConfigManager class that centralizes all configuration
loading and access, eliminating redundant file reads and providing a single source of truth
for application configuration.
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from utils.taxonomy import load_taxonomy_file

# Load environment variables at module level
load_dotenv()


class ConfigManager:
    """
    Singleton configuration manager that provides centralized access to application configuration.

    This class loads the base configuration from settings.yaml and environment variables,
    providing methods to:
    - Get configuration values using dot notation (e.g., 'database.host')
    - Override settings programmatically
    - Cache loaded taxonomy files to avoid redundant I/O
    - Access API keys and environment-specific settings
    """

    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        """Ensure only one instance of ConfigManager exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the ConfigManager if not already initialized."""
        if not hasattr(self, "_initialized"):
            self._config: Dict[str, Any] = {}
            self._taxonomy_cache: Dict[str, Dict[str, Any]] = {}
            self._config_lock = threading.Lock()
            self._env_vars: Dict[str, Any] = {}
            self._load_environment_variables()
            self._initialized = True

    def _load_environment_variables(self) -> None:
        """Load and cache environment variables."""
        self._env_vars = {
            # API Keys
            "OPENAI_KEY": os.getenv("OPENAI_KEY"),
            "GEMINI_KEY": os.getenv("GEMINI_KEY"),
            "DEEPSEEK_KEY": os.getenv("DEEPSEEK_KEY"),
            "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
            "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
            # Database settings
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "DB_PATH": os.getenv("DB_PATH", "database/math_agent.db"),
            # Application settings
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
            # Performance settings
            "DEFAULT_WORKERS": int(os.getenv("DEFAULT_WORKERS", "10")),
            "MAX_RETRIES": int(os.getenv("MAX_RETRIES", "3")),
        }

    def load_config(self, config_path: Path) -> None:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
        """
        with self._config_lock:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

            # Handle taxonomy loading with caching
            if isinstance(self._config.get("taxonomy"), str) and self._config[
                "taxonomy"
            ].endswith(".json"):
                taxonomy_path = self._config["taxonomy"]
                if taxonomy_path not in self._taxonomy_cache:
                    self._taxonomy_cache[taxonomy_path] = load_taxonomy_file(
                        taxonomy_path
                    )
                self._config["taxonomy"] = self._taxonomy_cache[taxonomy_path]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        First checks the loaded configuration, then falls back to environment variables.

        Args:
            key: Configuration key in dot notation (e.g., 'database.host', 'num_problems')
            default: Default value to return if key is not found

        Returns:
            The configuration value or default if not found

        Examples:
            >>> config_manager = ConfigManager()
            >>> config_manager.get('num_problems')
            10
            >>> config_manager.get('engineer_model.provider')
            'gemini'
            >>> config_manager.get('OPENAI_KEY')
            'sk-...'
            >>> config_manager.get('nonexistent.key', 'default_value')
            'default_value'
        """
        with self._config_lock:
            # First try to get from loaded configuration
            keys = key.split(".")
            value = self._config

            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                # Fall back to environment variables for single keys
                if len(keys) == 1 and key in self._env_vars:
                    return self._env_vars[key]
                return default

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: The provider name ('openai', 'gemini', 'deepseek', 'tavily')

        Returns:
            The API key or None if not found
        """
        key_mapping = {
            "openai": "OPENAI_KEY",
            "gemini": "GEMINI_KEY",
            "deepseek": "DEEPSEEK_KEY",
            "tavily": "TAVILY_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
        }

        env_key = key_mapping.get(provider.lower())
        if env_key:
            return self._env_vars.get(env_key)
        return None

    def get_model_config(self, agent_type: str) -> Dict[str, Any]:
        """
        Get model configuration for a specific agent type.

        Args:
            agent_type: The agent type ('engineer', 'checker', 'target')

        Returns:
            Dictionary containing provider and model_name
        """
        config_key = f"{agent_type}_model"
        return self.get(config_key, {})

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation
            value: Value to set

        Examples:
            >>> config_manager = ConfigManager()
            >>> config_manager.set('num_problems', 20)
            >>> config_manager.set('engineer_model.provider', 'openai')
        """
        with self._config_lock:
            keys = key.split(".")
            config_ref = self._config

            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]

            # Set the final key
            config_ref[keys[-1]] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values at once.

        Args:
            updates: Dictionary of key-value pairs to update

        Examples:
            >>> config_manager = ConfigManager()
            >>> config_manager.update({
            ...     'num_problems': 20,
            ...     'max_workers': 5,
            ...     'engineer_model.provider': 'openai'
            ... })
        """
        for key, value in updates.items():
            self.set(key, value)

    def get_all(self) -> Dict[str, Any]:
        """
        Get a copy of the entire configuration dictionary.

        Returns:
            A copy of the complete configuration
        """
        with self._config_lock:
            return self._config.copy()

    def load_taxonomy_file_cached(self, taxonomy_path: str) -> Dict[str, Any]:
        """
        Load a taxonomy file with caching to avoid redundant I/O.

        Args:
            taxonomy_path: Path to the taxonomy JSON file

        Returns:
            The loaded taxonomy data
        """
        with self._config_lock:
            if taxonomy_path not in self._taxonomy_cache:
                self._taxonomy_cache[taxonomy_path] = load_taxonomy_file(taxonomy_path)
            return self._taxonomy_cache[taxonomy_path]

    def clear_cache(self) -> None:
        """Clear the taxonomy cache (useful for testing or reloading)."""
        with self._config_lock:
            self._taxonomy_cache.clear()


# Global instance for easy access
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """
    Get the global ConfigManager instance.

    Returns:
        The singleton ConfigManager instance
    """
    return config_manager
