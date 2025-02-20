"""
Flask-SocketIO setup and event handlers.
This module initializes the WebSocket connection and sets up all event handlers.
Relies on Foundry VTT for session management and user authentication.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Socket.IO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

@socketio.on('connect')
async def handle_connect():
    """
    Handle new client connections.
    Expects Foundry user ID in connection parameters.
    """
    try:
        user_id = request.args.get('userId')
        if not user_id:
            logger.error("Connection attempt without userId")
            return False
        
        # Use Foundry's user ID as the room for message routing
        join_room(user_id)
        logger.info(f"Client connected: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_connect: {str(e)}")
        return False

@socketio.on('disconnect')
async def handle_disconnect():
    """Handle client disconnections"""
    try:
        user_id = request.args.get('userId')
        if user_id:
            leave_room(user_id)
            logger.info(f"Client disconnected: {user_id}")
    except Exception as e:
        logger.error(f"Error in handle_disconnect: {str(e)}")

async def _handle_typing_status(user_id: str, is_typing: bool):
    """Update typing status for a user"""
    emit('typing_status', {'isTyping': is_typing}, room=user_id)

@socketio.on('query')
async def handle_query(data):
    """Handle general queries"""
    try:
        user_id = request.args.get('userId')
        logger.info(f"Received query from {user_id}: {data.get('content', '')[:100]}...")
        
        # Set typing status
        await _handle_typing_status(user_id, True)
        
        # Temporary placeholder response
        emit('query_response', {
            'content': 'Query handling is being reimplemented. Please try again later.',
            'status': 'pending'
        }, room=user_id)
        
    except Exception as e:
        logger.error(f"Error in handle_query: {str(e)}")
        emit('error', {
            'error': "Internal server error processing query",
            'request_id': data.get('request_id')
        }, room=user_id)
    finally:
        if user_id:
            await _handle_typing_status(user_id, False)

@socketio.on('character_creation_start')
async def handle_character_creation(data):
    """Handle character creation events"""
    try:
        user_id = request.args.get('userId')
        logger.info(f"Starting character creation for {user_id}")
        
        await _handle_typing_status(user_id, True)
        
        # Temporary placeholder response
        emit('character_creation_response', {
            'status': 'pending',
            'message': 'Character creation system is being reimplemented. Please try again later.'
        }, room=user_id)
        
    except Exception as e:
        logger.error(f"Error in handle_character_creation: {str(e)}")
        emit('error', {
            'error': "Internal server error during character creation",
            'request_id': data.get('request_id')
        }, room=user_id)
    finally:
        if user_id:
            await _handle_typing_status(user_id, False)

@socketio.on('character_level_up')
async def handle_level_up(data):
    """Handle character level up events"""
    try:
        user_id = request.args.get('userId')
        logger.info(f"Processing level up for {user_id}")
        
        await _handle_typing_status(user_id, True)
        
        # Temporary placeholder response
        emit('level_up_response', {
            'status': 'pending',
            'message': 'Level up system is being reimplemented. Please try again later.'
        }, room=user_id)
        
    except Exception as e:
        logger.error(f"Error in handle_level_up: {str(e)}")
        emit('error', {
            'error': "Internal server error during level up",
            'request_id': data.get('request_id')
        }, room=user_id)
    finally:
        if user_id:
            await _handle_typing_status(user_id, False)

@socketio.on('combat_turn')
async def handle_combat_turn(data):
    """Handle combat turn events"""
    try:
        user_id = request.args.get('userId')
        logger.info(f"Processing combat turn for {user_id}")
        
        await _handle_typing_status(user_id, True)
        
        # Temporary placeholder response
        emit('combat_suggestion', {
            'status': 'pending',
            'message': 'Combat assistance system is being reimplemented. Please try again later.'
        }, room=user_id)
        
    except Exception as e:
        logger.error(f"Error in handle_combat_turn: {str(e)}")
        emit('error', {
            'error': "Internal server error during combat",
            'request_id': data.get('request_id')
        }, room=user_id)
    finally:
        if user_id:
            await _handle_typing_status(user_id, False)

@socketio.on_error()
def error_handler(e):
    """Handle WebSocket errors"""
    logger.error(f"WebSocket error: {str(e)}")
    return False

@socketio.on_error_default
def default_error_handler(e):
    """Handle uncaught WebSocket errors"""
    logger.error(f"Uncaught WebSocket error: {str(e)}")
    return False 