import multiprocessing
import os

# Bind to 0.0.0.0:8000
bind = "0.0.0.0:8000"

# Worker Configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Timeouts
timeout = 120
keepalive = 5
