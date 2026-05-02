import logging
import os
from .constants import PROJECT_ROOT

def setup_logger():
    log_path = os.path.join(PROJECT_ROOT, "sentrytop_cli.log")
    
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Also log to stderr for critical errors if needed, 
    # but in a TUI we usually want to avoid this unless it's a fatal crash.
    return logging.getLogger("SentryTop")

logger = setup_logger()
