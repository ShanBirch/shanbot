#!/bin/bash
# Quick Instagram Inbox Check
# Simple wrapper script for checking Instagram DMs

echo "🚀 Starting Instagram Inbox Check..."
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Error: Python not found"
    exit 1
fi

# Run the checker
$PYTHON check_unread_instagram_messages.py "$@"
