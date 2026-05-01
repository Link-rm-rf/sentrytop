#!/bin/bash
# SentryTop Intel Weekly Update Cron Script

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Run the python update script
# We need to make sure we are in the project root or use absolute paths
cd "$PROJECT_ROOT/.."
python3 sentrytop/scripts/update_intel.py >> sentrytop/sentrytop_cli.log 2>&1

# Note: We don't need to restart the engine if it reloads the file periodically, 
# but currently it only loads at startup.
# The requirement didn't specify auto-reloading in the engine, 
# but it's a good idea for "production-grade".
# For now, we'll just update the file.
