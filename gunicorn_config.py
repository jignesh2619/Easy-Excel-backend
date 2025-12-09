"""
Gunicorn configuration for LazyExcel Backend
"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes - Reduced for 512MB server
# Use only 2 workers to prevent OOM on small servers
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 300  # Increased timeout for large file processing
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "lazyexcel-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

