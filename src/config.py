import logging

# Logging configuration
def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

# Application constants
DEFAULT_TUNNEL_TIMEOUT = 10
PROCESS_KILL_TIMEOUT = 1
MONITOR_TIMEOUT = 15
PROCESS_POLL_INTERVAL = 0.1 