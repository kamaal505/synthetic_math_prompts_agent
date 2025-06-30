"""
Logging configuration for the synthetic math prompts agent.

This module provides a centralized logging setup that can be used throughout
the application to replace print statements with proper logging.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "synthetic_math_prompts",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and handlers.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger instance
default_logger = setup_logger()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional logger name. If None, returns the default logger.

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return default_logger


def log_error(message: str, exception: Exception = None, logger: logging.Logger = None):
    """
    Log an error message with optional exception details.

    Args:
        message: Error message to log
        exception: Optional exception to include
        logger: Optional logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = default_logger

    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message)


def log_warning(message: str, logger: logging.Logger = None):
    """
    Log a warning message.

    Args:
        message: Warning message to log
        logger: Optional logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = default_logger

    logger.warning(message)


def log_info(message: str, logger: logging.Logger = None):
    """
    Log an info message.

    Args:
        message: Info message to log
        logger: Optional logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = default_logger

    logger.info(message)


def log_debug(message: str, logger: logging.Logger = None):
    """
    Log a debug message.

    Args:
        message: Debug message to log
        logger: Optional logger instance. If None, uses default logger.
    """
    if logger is None:
        logger = default_logger

    logger.debug(message)
