"""
Frinny Backend Server - Application Entry Point

This module serves as the entry point for running the Frinny backend server.
It creates and runs the Flask application with the appropriate configuration.
"""

from gevent import monkey
monkey.patch_all()

from app import create_app
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

app = create_app()

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5001), app, handler_class=WebSocketHandler)
    print('Starting Frinny backend server on http://0.0.0.0:5001')
    http_server.serve_forever() 