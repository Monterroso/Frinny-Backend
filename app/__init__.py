"""
Frinny Backend Server - Main Application Module

This module initializes the Flask application and sets up all necessary extensions
and configurations for the Frinny Foundry VTT module backend.
"""

from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv

# Initialize Flask-SocketIO
socketio = SocketIO()

# Initialize Flask-Limiter
limiter = None

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
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Initialize Flask-SocketIO with app
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize Flask-Limiter
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['REDIS_URL']
    )

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for container orchestration."""
        return jsonify({
            'status': 'healthy',
            'environment': config_name
        })
    
    # Register blueprints (to be implemented)
    # from .routes import query_bp, character_bp, combat_bp
    # app.register_blueprint(query_bp)
    # app.register_blueprint(character_bp)
    # app.register_blueprint(combat_bp)
    
    # Register error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        """Global error handler for the application."""
        response = {
            'error': {
                'code': getattr(error, 'code', 500),
                'message': str(error),
                'details': getattr(error, 'details', None)
            }
        }
        return response, getattr(error, 'code', 500)
    
    return app 