# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1  # Reduced to 1 to prevent OOM on 2GB RAM droplet
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 300  # 5 minutes - increased for large file processing
keepalive = 5

# Memory management
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Process naming
proc_name = "easyexcel-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Performance
max_requests = 1000
max_requests_jitter = 50
preload_app = False






