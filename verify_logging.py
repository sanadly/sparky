import sys
import os
import logging
import json

# Add current directory to path
sys.path.append(os.getcwd())

from backend.logger import setup_logging

def verify_logging():
    setup_logging()
    logger = logging.getLogger("test_logger")
    
    # We need to capture stdout/stderr to check the format
    # But for simplicity, let's just run it and manually check or use a pipe in run_command
    logger.info("Test JSON log message", extra={"user_id": "123", "action": "test"})

if __name__ == "__main__":
    verify_logging()