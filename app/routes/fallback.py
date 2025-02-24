"""
HTTP fallback routes for when WebSocket connection is not available.
These routes provide basic functionality when WebSocket fails.
"""

from flask import Blueprint, request, jsonify
from app.config.websocket_config import WebSocketConfig
import logging
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)

# Create blueprint
fallback_bp = Blueprint('fallback', __name__)

@fallback_bp.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """Handle feedback when WebSocket is not available."""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            logger.warning(f"Missing userId in feedback request: {data}")
            return jsonify({
                'status': 'error',
                'message': 'userId is required'
            }), 400
            
        # Process feedback (implement proper storage later)
        logger.info(f"Received feedback from userId={user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received',
            'fallback_endpoints': WebSocketConfig.get_websocket_urls()
        })
        
    except Exception as e:
        logger.error(f"Error handling feedback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'fallback_endpoints': WebSocketConfig.get_websocket_urls()
        }), 500

@fallback_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint that includes available endpoints."""
    logger.debug("Health check requested")
    return jsonify({
        'status': 'healthy',
        'available_endpoints': WebSocketConfig.get_websocket_urls()
    }) 