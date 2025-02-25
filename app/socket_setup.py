"""
Flask-SocketIO setup and event handlers.
This module initializes the WebSocket connection and sets up all event handlers.
Relies on Foundry VTT for session management and user authentication.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from app.config.websocket_config import WebSocketConfig
import uuid
import time
import json
import asyncio
from app.config.logging_config import get_logger
from app.agent.agent import lang_graph_handler

# Get module logger
logger = get_logger(__name__)

def format_data(data):
    """Format data in a readable way"""
    if isinstance(data, dict):
        # Format dictionary in a readable way
        return json.dumps(data, indent=2)
    return str(data)

# Initialize Socket.IO with configuration
config = WebSocketConfig()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=False,  # Disable SocketIO's internal logging
    engineio_logger=False,  # Disable Engine.IO's internal logging
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
            logger.warning(f"Connection attempt without userId from {sid}")
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
        
        logger.info(f"Client connected: userId={user_id}, sid={sid}")
        emit('connection_established', response, room=user_id)
        
        return True
        
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
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
            
            logger.info(f"Client disconnected: userId={user_id}, sid={sid}")
            emit('disconnect_acknowledged', response, room=user_id)
        
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")

async def handle_generic_event_async(event_type, data, user_id, response_event=None, message_field='message'):
    """
    Generic handler for socket events - async implementation
    
    Args:
        event_type: Type of event (query, character_creation, etc.)
        data: Data received from client
        user_id: User ID from the request
        response_event: Event name to emit response (defaults to event_type + '_response')
        message_field: Field name to use for the message in response ('message' or 'content')
        
    Returns:
        None
    """
    try:
        request_id = data.get('request_id', str(uuid.uuid4()))
        
        logger.info(f"Processing {event_type} request from userId={user_id}, request_id={request_id}")
        
        # Default response event name if not provided
        if response_event is None:
            response_event = f"{event_type}_response"
        
        # Process the event using LangGraphHandler
        response = await lang_graph_handler.process_event(event_type, data, user_id)
        
        # Ensure the response has the correct message field
        if message_field not in response and 'content' in response:
            response[message_field] = response.pop('content')
        elif message_field not in response and 'message' in response:
            response[message_field] = response.pop('message')
        
        logger.info(f"Sending {response_event} to userId={user_id}, request_id={request_id}")
        socketio.emit(response_event, response, room=user_id)
        
    except Exception as e:
        error_response = {
            'error': f"Internal server error during {event_type}",
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        logger.error(f"Error in {event_type}: {str(e)}")
        socketio.emit('error', error_response, room=user_id)

def handle_generic_event(event_type, data, user_id, response_event=None, message_field='message'):
    """
    Synchronous wrapper for handle_generic_event_async that properly runs the coroutine
    
    Args:
        Same as handle_generic_event_async
    """
    # Create an event loop for this thread if it doesn't exist
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in this thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run the coroutine until it completes
    try:
        loop.run_until_complete(handle_generic_event_async(
            event_type, data, user_id, response_event, message_field
        ))
    except Exception as e:
        logger.error(f"Error in handle_generic_event: {str(e)}")
        # Send error response
        error_response = {
            'error': f"Internal server error during {event_type}",
            'request_id': data.get('request_id', str(uuid.uuid4())),
            'timestamp': int(time.time() * 1000)
        }
        socketio.emit('error', error_response, room=user_id)

@socketio.on('query')
def handle_query(data):
    """Handle general queries"""
    user_id = request.args.get('userId')
    # Send immediate acknowledgment
    ack = {
        'status': 'processing',
        'request_id': data.get('request_id', str(uuid.uuid4())),
        'timestamp': int(time.time() * 1000)
    }
    emit('query_ack', ack, room=user_id)
    
    # Process in background
    socketio.start_background_task(
        handle_generic_event, 
        'query', data, user_id, 
        response_event='query_response', 
        message_field='content'
    )

@socketio.on('character_creation_start')
def handle_character_creation(data):
    """Handle character creation events"""
    user_id = request.args.get('userId')
    socketio.start_background_task(
        handle_generic_event, 
        'character_creation', data, user_id, 
        response_event='character_creation_response'
    )

@socketio.on('level_up')
def handle_level_up(data):
    """Handle level up events"""
    user_id = request.args.get('userId')
    socketio.start_background_task(
        handle_generic_event, 
        'level_up', data, user_id, 
        response_event='level_up_response'
    )

@socketio.on('combat_turn')
def handle_combat_turn(data):
    """Handle combat turn events"""
    user_id = request.args.get('userId')
    socketio.start_background_task(
        handle_generic_event, 
        'combat_turn', data, user_id, 
        response_event='combat_turn_response'
    )

@socketio.on('combat_start')
def handle_combat_start(data):
    """Handle combat start events"""
    user_id = request.args.get('userId')
    socketio.start_background_task(
        handle_generic_event, 
        'combat_start', data, user_id, 
        response_event='combat_start_response'
    )

@socketio.on('feedback')
def handle_feedback(data):
    """
    Handle user feedback on responses
    
    Args:
        data: Feedback data with fields:
            - request_id: ID of the original request
            - rating: User rating (1-5)
            - comment: Optional user comment
            - context_id: Context ID of the conversation
    """
    try:
        user_id = request.args.get('userId')
        request_id = data.get('request_id')
        rating = data.get('rating')
        
        logger.info(f"Received feedback from userId={user_id}, request_id={request_id}, rating={rating}")
        
        # Send acknowledgment immediately
        response = {
            'status': 'success',
            'message': 'Feedback received',
            'request_id': request_id,
            'timestamp': int(time.time() * 1000)
        }
        emit('feedback_response', response, room=user_id)
        
        # Process feedback in background if context_id is provided
        if 'context_id' in data:
            socketio.start_background_task(
                handle_generic_event,
                'feedback', data, user_id
            )
        
    except Exception as e:
        error_response = {
            'error': 'Error processing feedback',
            'request_id': data.get('request_id'),
            'timestamp': int(time.time() * 1000)
        }
        logger.error(f"Error in feedback: {str(e)}")
        emit('error', error_response, room=user_id)

@socketio.on_error()
def error_handler(e):
    """Handle WebSocket errors"""
    logger.error(f"WebSocket error: {str(e)}")
    try:
        error_response = {
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
        emit('error', error_response)
    except Exception as err:
        logger.error(f"Error in error handler: {str(err)}")
    return False

@socketio.on_error_default
def default_error_handler(e):
    """Handle uncaught WebSocket errors"""
    logger.error(f"Uncaught WebSocket error: {str(e)}")
    try:
        error_response = {
            'error': str(e),
            'timestamp': int(time.time() * 1000)
        }
        emit('error', error_response)
    except Exception as err:
        logger.error(f"Error in default error handler: {str(err)}")
    return False 