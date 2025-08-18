# Gunicorn configuration for A³E API production deployment

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/a3e/access.log"
errorlog = "/var/log/a3e/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'a3e-api'

# Server mechanics
daemon = False
pidfile = '/var/run/a3e/gunicorn.pid'
user = 'www-data'
group = 'www-data'
tmp_upload_dir = None

# SSL (handled by NGINX)
# keyfile = None
# certfile = None

# Environment variables
raw_env = [
    'ENVIRONMENT=production',
    'PYTHONPATH=/opt/a3e',
]

# Preload application for better performance
def when_ready(server):
    server.log.info("A³E API server is ready. Serving requests.")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
