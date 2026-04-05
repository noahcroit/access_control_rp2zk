#!/bin/bash
# Internet connectivity check script for KMITL
# Target to ping for internet check
TARGET="8.8.8.8"
# Location of the authentication script
PYTHON_SCRIPT="/home/pi/Auto-Authen-KMITL/authen.py"

# Try to ping the target once with a 5-second timeout
if ! ping -c 1 -W 5 $TARGET > /dev/null 2>&1; then
    echo "$(date): Internet is down. Running authentication script..."
    # Ensure we run with python3 as standard on Raspbian
    /usr/bin/python3 "$PYTHON_SCRIPT"
else
    echo "$(date): Internet is up."
fi
