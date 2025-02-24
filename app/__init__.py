"""
Frinny Backend Server - Main Application Module

This module initializes the Flask application and sets up all necessary extensions
and configurations for the Frinny Foundry VTT module backend.
"""

from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from app.socket_setup import socketio
from app.routes.fallback import fallback_bp
from app.config.logging_config import setup_logging, get_logger

# Set up logging
logger = get_logger(__name__)

def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str): The name of the configuration to use (development, production, testing)
        
    Returns:
        Flask: The configured Flask application instance
    """
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    setup_logging()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app based on environment
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Basic configurations
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # Register blueprints
    app.register_blueprint(fallback_bp)

    # Initialize SocketIO with the app
    socketio.init_app(app)
    
    logger.info(f"Flask application started in {config_name} mode")

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for container orchestration."""
        return jsonify({
            'status': 'healthy',
            'environment': config_name
        })
    
    return app 