import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup and configure logger."""
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)