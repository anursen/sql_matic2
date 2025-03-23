import logging
import sys
import os
from pathlib import Path

# Define log directory and file
log_dir = Path("/Users/anursen/Documents/sql_matic2/logs")
log_file = log_dir / "sql_matic.log"

# Create logs directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
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
