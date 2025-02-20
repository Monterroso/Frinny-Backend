"""
WebSocket configuration for Frinny Backend Server.
Handles WebSocket URLs and fallback options.
"""

import os
from typing import List, Dict

class WebSocketConfig:
    """Configuration class for WebSocket settings."""
    
    @staticmethod
    def get_websocket_urls() -> Dict[str, List[str]]:
        """
        Get WebSocket URLs with fallbacks based on environment.
        
        Returns:
            Dict containing WebSocket and HTTP URLs for different environments
        """
        # Base URLs for different environments
        DEVELOPMENT = {
            'ws': [
                'ws://localhost:5001',
                'ws://127.0.0.1:5001'
            ],
            'http': [
                'http://localhost:5001',
                'http://127.0.0.1:5001'
            ]
        }
        
        PRODUCTION = {
            'ws': [
                'wss://api.frinny.ai',
                'ws://api.frinny.ai'
            ],
            'http': [
                'https://api.frinny.ai',
                'http://api.frinny.ai'
            ]
        }
        
        # Get environment from env var, default to development
        env = os.getenv('FLASK_ENV', 'development')
        
        # Return appropriate URLs based on environment
        return PRODUCTION if env == 'production' else DEVELOPMENT
    
    @staticmethod
    def get_socket_options() -> Dict:
        """
        Get Socket.IO client configuration options.
        
        Returns:
            Dict containing Socket.IO client options
        """
        return {
            'reconnection': True,
            'reconnectionAttempts': 5,
            'reconnectionDelay': 1000,
            'reconnectionDelayMax': 5000,
            'timeout': 20000,
            'autoConnect': True,
            'transports': ['websocket', 'polling']
        } 