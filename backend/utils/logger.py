import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Union

from backend.config.config import config

# Log level mapping
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def _get_level(level: Union[str, int]) -> int:
    """Convert string level to logging level constant"""
    if isinstance(level, int):
        return level
    return LEVELS.get(level.upper(), logging.INFO)

def initialize_logger():
    """Initialize and configure the application-wide logger"""
    # Get configuration from config.yaml
    log_level = config.get("logging", "level", "INFO")
    log_format = config.get("logging", "format", "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    log_file = config.get("logging", "file", "logs/app.log")
    max_size = config.get("logging", "max_size", 10485760)  # 10MB default
    backup_count = config.get("logging", "backup_count", 5)
    
    # Configure root logger
    root_logger = logging.getLogger("sql_matic")
    root_logger.setLevel(_get_level(log_level))
    root_logger.handlers = []  # Clear existing handlers
    
    # Set up formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size, 
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

# Initialize the global logger once
logger = initialize_logger()

# Convenience functions for direct access to logger methods
def debug(message: str, *args, **kwargs):
    """Log a debug message"""
    logger.debug(message, *args, **kwargs)

def info(message: str, *args, **kwargs):
    """Log an info message"""
    logger.info(message, *args, **kwargs)

def warning(message: str, *args, **kwargs):
    """Log a warning message"""
    logger.warning(message, *args, **kwargs)

def error(message: str, *args, **kwargs):
    """Log an error message"""
    logger.error(message, *args, **kwargs)

def critical(message: str, *args, **kwargs):
    """Log a critical message"""
    logger.critical(message, *args, **kwargs)

def exception(message: str, *args, **kwargs):
    """Log an exception with traceback"""
    logger.exception(message, *args, **kwargs)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that inherits settings from the root logger
    
    Args:
        name: Logger name
        
    Returns:
        A configured Logger instance
    """
    # This creates a child logger that inherits the configuration from our root logger
    return logging.getLogger(f"sql_matic.{name}")
