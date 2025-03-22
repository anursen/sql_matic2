import logging
import sys

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger
logger = logging.getLogger("sql_matic")

# Define shortcut functions
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

def get_logger(name: str):
    """Get a child logger with the specified name"""
    return logging.getLogger(f"sql_matic.{name}")
