from pathlib import Path
from typing import Any, Dict

from utils.config_manager import get_config_manager


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file using the centralized ConfigManager.

    This function is now a wrapper around the ConfigManager to maintain
    backward compatibility while providing centralized configuration management.

    Args:
        config_path: Path to the configuration YAML file

    Returns:
        Dictionary containing the loaded configuration
    """
    config_manager = get_config_manager()
    config_manager.load_config(config_path)
    return config_manager.get_all()
