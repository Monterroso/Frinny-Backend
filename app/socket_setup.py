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

def handle_generic_event(event_type, data, response_event=None, message_field='message'):
    """
    Generic handler for socket events
    
    Args:
        event_type: Type of event (query, character_creation, etc.)
        data: Data received from client
        response_event: Event name to emit response (defaults to event_type + '_response')
        message_field: Field name to use for the message in response ('message' or 'content')
        
    Returns:
        None
    """
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        
        # Default response event name if not provided
        if response_event is None:
            response_event = f"{event_type}_response"
        
        log_event(event_type, f'Processing {event_type} request', data)
        
        # Create response with common fields
        response = {
            'request_id': request_id,
            'status': 'pending',
            'timestamp': int(time.time() * 1000)
        }
        
        # Add message with appropriate field name
        # Default placeholder message
        message = f'{event_type.replace("_", " ").title()} system is being reimplemented. Please try again later.'
        
        # Special case messages for specific events
        if event_type == 'combat_start':
            message = 'Combat start system is being implemented. Please try again later.'
        
        response[message_field] = message
        
        log_event(response_event, f'Sending {event_type} response', response)
        emit(response_event, response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': f"Internal server error during {event_type}",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        log_event(f'{event_type}_error', f'Error in {event_type}', error_response, str(e))
        emit('error', error_response, room=user_id)

@socketio.on('query')
def handle_query(data):
    """Handle general queries"""
    handle_generic_event('query', data, message_field='content')

@socketio.on('character_creation_start')
def handle_character_creation(data):
    """Handle character creation events"""
    handle_generic_event('character_creation', data, response_event='character_creation_response')

@socketio.on('level_up')
def handle_level_up(data):
    """Handle character level up events"""
    handle_generic_event('level_up', data)

@socketio.on('combat_turn')
def handle_combat_turn(data):
    """Handle combat turn events"""
    handle_generic_event('combat_turn', data, response_event='combat_suggestion')

@socketio.on('combat_start')
def handle_combat_start(data):
    """Handle combat start events"""
    handle_generic_event('combat_start', data, response_event='combat_suggestion')

@socketio.on('feedback')
def handle_feedback(data):
    """Handle feedback events"""
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id', str(uuid.uuid4()))
        logger.info(f"Processing feedback from {user_id}")
        
        # Send response directly
        emit('feedback_response', {
            'request_id': request_id,
            'status': 'success',
            'message': 'Feedback received. Thank you for your input.',
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