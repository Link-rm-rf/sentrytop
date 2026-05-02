#!/usr/bin/env python3
import sys
import os

# Add the parent directory to sys.path to allow absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.app import SentryTopApp
from ui.utils.logger import logger

def main():
    try:
        app = SentryTopApp()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal startup error: {e}", exc_info=True)
        print(f"Fatal error: {e}. Check sentrytop_cli.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
