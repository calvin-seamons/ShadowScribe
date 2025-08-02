"""
Logging utilities for the D&D RAG Chunker
"""

import logging
from pathlib import Path
from config.settings import Config


def setup_logging(config: Config):
    """Setup enhanced logging with file and console output"""
    log_level = getattr(logging, config.log_level.upper())
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Setup file handler
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
