"""
Flask-SocketIO setup and event handlers.
This module initializes the WebSocket connection and sets up all event handlers.
Relies on Foundry VTT for session management and user authentication.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, current_app
import logging
import logging.config
from app.config.websocket_config import WebSocketConfig
import uuid
import time
import json
import sys

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '\n%(asctime)s | %(levelname)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'detailed',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        'socket_events': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
})

logger = logging.getLogger('socket_events')

def format_log_data(data):
    """Format data for logging in a readable way"""
    if isinstance(data, dict):
        # Format dictionary in a readable way
        return json.dumps(data, indent=2)
    return str(data)

def log_event(event_type, details, data=None, error=None):
    """
    Structured logging for socket events
    
    Args:
        event_type: Type of event (connect, disconnect, query, etc.)
        details: Description of what's happening
        data: Optional data associated with event
        error: Optional error information
    """
    log_lines = [
        "=" * 50,
        f"Socket Event: {event_type}",
        f"Details: {details}",
        f"SID: {request.sid}",
        f"UserID: {request.args.get('userId', 'Not provided')}"
    ]
    
    if data:
        log_lines.extend([
            "Data:",
            format_log_data(data)
        ])
    
    if error:
        log_lines.extend([
            "Error:",
            format_log_data(error)
        ])
    
    log_lines.append("=" * 50)
    logger.info("\n".join(log_lines))

# Initialize Socket.IO with configuration
config = WebSocketConfig()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    **config.get_socket_options()
)

@socketio.on('connect')
def handle_connect():
    """
    Handle new client connections.
    Expects Foundry user ID in connection parameters.
    Note: Changed from to sync as Socket.IO doesn't support handlers
    """
    try:
        user_id = request.args.get('userId')
        sid = request.sid
        
        if not user_id:
            log_event('connect', 'Connection attempt without userId', error='Missing userId')
            return False
        
        # Join room using userId only
        join_room(user_id)
        
        # Send connection success event with available endpoints
        response = {
            'status': 'connected',
            'endpoints': config.get_websocket_urls(),
            'userId': user_id,
            'sid': sid,
            'timestamp': int(time.time() * 1000)
        }
        
        log_event('connect', 'Client connected successfully', response)
        emit('connection_established', response, room=user_id)
        
        return True
        
    except Exception as e:
        log_event('connect', 'Connection error', error=str(e))
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections"""
    try:
        user_id = request.args.get('userId')
        sid = request.sid
        
        if user_id:
            leave_room(user_id)
            
            # Emit disconnect event to client
            response = {
                'status': 'disconnected',
                'userId': user_id,
                'sid': sid,
                'timestamp': int(time.time() * 1000)
            }
            
            log_event('disconnect', 'Client disconnected', response)
            emit('disconnect_acknowledged', response, room=user_id)
        
    except Exception as e:
        log_event('disconnect', 'Disconnect error', error=str(e))

@socketio.on('query')
def handle_query(data):
    """Handle general queries"""
    try:
        user_id = request.args.get('userId')
        sid = request.sid
        request_id = data.get('request_id', str(uuid.uuid4()))
        
        log_event('query', 'Received new query', {
            'request_id': request_id,
            'query_data': data
        })
        
        # Acknowledge receipt of query
        ack_response = {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }
        log_event('query_received', 'Query acknowledgment sent', ack_response)
        emit('query_received', ack_response, room=user_id)
        
        # Temporary placeholder response
        response = {
            'request_id': request_id,
            'content': 'Query handling is being reimplemented. Please try again later.',
            'status': 'pending',
            'timestamp': int(time.time() * 1000)
        }
        log_event('query_response', 'Sending query response', response)
        emit('query_response', response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': "Internal server error processing query",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event('query_error', 'Error processing query', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('character_creation_start')
def handle_character_creation(data):
    """Handle character creation events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        log_event('character_creation', 'Starting character creation', data)
        
        # Acknowledge receipt
        emit('character_creation_received', {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }, room=user_id)
        
        # Temporary placeholder response
        response = {
            'request_id': request_id,
            'status': 'pending',
            'message': 'Character creation system is being reimplemented. Please try again later.',
            'timestamp': int(time.time() * 1000)
        }
        log_event('character_creation_response', 'Sending character creation response', response)
        emit('character_creation_response', response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': "Internal server error during character creation",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event('character_creation_error', 'Error in character creation', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('level_up')
def handle_level_up(data):
    """Handle character level up events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        log_event('level_up', 'Processing level up request', data)
        
        # Acknowledge receipt
        ack_response = {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }
        log_event('level_up_received', 'Level up request acknowledged', ack_response)
        emit('level_up_received', ack_response, room=user_id)
        
        # Temporary placeholder response
        response = {
            'request_id': request_id,
            'status': 'pending',
            'message': 'Level up system is being reimplemented. Please try again later.',
            'timestamp': int(time.time() * 1000)
        }
        log_event('level_up_response', 'Sending level up response', response)
        emit('level_up_response', response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': "Internal server error during level up",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event('level_up_error', 'Error in level up', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('combat_turn')
def handle_combat_turn(data):
    """Handle combat turn events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        log_event('combat_turn', 'Processing combat turn request', data)
        
        # Acknowledge receipt
        ack_response = {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_turn_received', 'Combat turn request acknowledged', ack_response)
        emit('combat_turn_received', ack_response, room=user_id)
        
        # Temporary placeholder response
        response = {
            'request_id': request_id,
            'status': 'pending',
            'message': 'Combat assistance system is being reimplemented. Please try again later.',
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_suggestion', 'Sending combat turn response', response)
        emit('combat_suggestion', response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': "Internal server error during combat",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_turn_error', 'Error in combat turn', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('combat_start')
def handle_combat_start(data):
    """Handle combat start events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        log_event('combat_start', 'Processing combat start request', data)
        
        # Acknowledge receipt
        ack_response = {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_start_received', 'Combat start request acknowledged', ack_response)
        emit('combat_start_received', ack_response, room=user_id)
        
        # Process combat data and emit response
        response = {
            'request_id': request_id,
            'status': 'pending',
            'message': 'Combat start system is being implemented',
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_suggestion', 'Sending combat start response', response)
        emit('combat_suggestion', response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': "Internal server error during combat start",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event('combat_start_error', 'Error in combat start', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('feedback')
def handle_feedback(data):
    """Handle feedback events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        logger.info(f"Processing feedback from {user_id}")
        
        # Acknowledge receipt
        emit('feedback_received', {
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }, room=user_id)
        
        # Send response
        emit('feedback_response', {
            'request_id': request_id,
            'status': 'success',
            'message': 'Feedback received',
            'timestamp': int(time.time() * 1000)
        }, room=user_id)
        
    except Exception as e:
        logger.error(f"Error in handle_feedback: {str(e)}")
        emit('error', {
            'error': "Internal server error processing feedback",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }, room=user_id)

@socketio.on_error()
def error_handler(e):
    """Handle WebSocket errors"""
    log_event('websocket_error', 'WebSocket error occurred', error=str(e))
    try:
        error_response = {
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
        emit('error', error_response)
    except Exception as err:
        log_event('error_handler_error', 'Error in error handler', error=str(err))
    return False

@socketio.on_error_default
def default_error_handler(e):
    """Handle uncaught WebSocket errors"""
    log_event('uncaught_websocket_error', 'Uncaught WebSocket error', error=str(e))
    try:
        error_response = {
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
        emit('error', error_response)
    except Exception as err:
        log_event('default_error_handler_error', 'Error in default error handler', error=str(err))
    return False 