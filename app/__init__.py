"""
Frinny Backend Server - Main Application Module

This module initializes the Flask application and sets up all necessary extensions
and configurations for the Frinny Foundry VTT module backend.
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
import logging
import json
import time
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask-SocketIO
socketio = SocketIO(
    logger=True,
    engineio_logger=True,
    cors_allowed_origins="*",
    async_mode='eventlet'
)

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

    # Initialize SocketIO with the app
    socketio.init_app(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        user_id = request.args.get('userId')
        if not user_id:
            logger.error('Connection attempt without userId')
            return False
        
        logger.info(f'Client connected: {user_id}')
        return True

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        user_id = request.args.get('userId')
        logger.info(f'Client disconnected: {user_id}')

    @socketio.on('query')
    def handle_query(data):
        """
        Handle query messages from clients.
        
        Args:
            data (dict): The query data from the client
        """
        user_id = request.args.get('userId')
        request_id = data.get('request_id')
        
        # Send typing status
        emit('typing_status', {
            'isTyping': True
        }, room=user_id)
        
        # TODO: Process query with AI service
        response = {
            'type': 'query_response',
            'request_id': request_id,
            'content': 'Query received and processed',  # Replace with actual AI response
            'timestamp': int(time.time() * 1000),
            'message_id': str(uuid.uuid4()),
            'show_feedback': True
        }
        
        emit('query_response', response, room=user_id)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for container orchestration."""
        return jsonify({
            'status': 'healthy',
            'environment': config_name
        })
    
    return app 