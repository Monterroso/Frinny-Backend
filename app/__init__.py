"""
Frinny Backend Server - Main Application Module

This module initializes the Flask application and sets up all necessary extensions
and configurations for the Frinny Foundry VTT module backend.
"""

from flask import Flask, jsonify
import os
from dotenv import load_dotenv
import logging
from app.socket_setup import socketio
from app.routes.fallback import fallback_bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for container orchestration."""
        return jsonify({
            'status': 'healthy',
            'environment': config_name
        })
    
    return app 