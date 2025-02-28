"""
Simple logging configuration for Frinny Backend.

This module provides a basic logging setup that can be used throughout the application.
"""

import os
import sys
import logging

def setup_logging():
    """
    Configure a simple logging setup for the application.
    
    Sets up a console handler with a consistent format and appropriate log level
    based on the environment.
    """
    # Determine environment and set log level
    env = os.getenv('FLASK_ENV', 'development')
    log_level = logging.DEBUG if env == 'development' else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    
    # Set levels for some verbose libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    # Add PyMongo loggers to reduce verbose heartbeat logs
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('pymongo.topology').setLevel(logging.WARNING)
    
    # Return the root logger for convenience
    return logging.getLogger()

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Name for the logger, typically __name__ of the module
        
    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(name) 