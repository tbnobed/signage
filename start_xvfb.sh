#!/bin/bash

# Start Xvfb script for digital signage client
# This script ensures Xvfb starts properly and is managed correctly

# Kill any existing Xvfb processes on display :99
pkill -f "Xvfb :99" 2>/dev/null || true

# Wait a moment for cleanup
sleep 1

# Start Xvfb in background
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX &

# Save PID for later cleanup
echo $! > /tmp/xvfb.pid

# Wait for Xvfb to start
sleep 2

# Verify Xvfb is running
if ps -p $(cat /tmp/xvfb.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "Xvfb started successfully on display :99"
    exit 0
else
    echo "Failed to start Xvfb"
    exit 1
fi