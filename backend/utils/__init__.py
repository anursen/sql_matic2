import logging
import sys

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger
logger = logging.getLogger("sql_matic")

from .logger import (
    logger, debug, info, warning, error, critical, exception,
    get_logger
)

__all__ = [
    'logger', 'debug', 'info', 'warning', 'error', 'critical', 'exception',
    'get_logger'
]
