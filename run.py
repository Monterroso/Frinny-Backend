"""
Frinny Backend Server - Application Entry Point

This module serves as the entry point for running the Frinny backend server.
It creates and runs the Flask application with the appropriate configuration.
"""

from gevent import monkey
monkey.patch_all()

import os
from dotenv import load_dotenv
from app import create_app
from app.socket_setup import socketio
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

# Load environment variables
load_dotenv()

# Get environment setting
env = os.getenv('FLASK_ENV', 'development')

app = create_app()

if __name__ == '__main__':
    if env.lower() == 'production':
        # Production mode: Use WSGIServer
        http_server = WSGIServer(('0.0.0.0', 5001), app, handler_class=WebSocketHandler)
        print(f'Starting Frinny backend server in PRODUCTION mode on http://0.0.0.0:5001')
        http_server.serve_forever()
    else:
        # Development mode: Use Flask's built-in server with debug mode
        print(f'Starting Frinny backend server in DEVELOPMENT mode on http://0.0.0.0:5001')
        socketio.run(app, host='0.0.0.0', port=5001, debug=True) 