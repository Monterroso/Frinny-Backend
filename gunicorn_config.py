"""
Gunicorn configuration file for Frinny Backend Server.

This configuration file sets up Gunicorn to serve the Flask application
with appropriate settings for development and production environments.
Configured to use eventlet worker for WebSocket support.
"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker processes - using single worker for WebSocket sticky sessions
workers = 1
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120  # Increased timeout for long-running WebSocket connections
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'  # More detailed logging for development

# Process naming
proc_name = 'frinny-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None 