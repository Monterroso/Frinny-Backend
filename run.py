"""
Frinny Backend Server - Application Entry Point

This module serves as the entry point for running the Frinny backend server.
It creates and runs the Flask application with the appropriate configuration.
"""

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001) 