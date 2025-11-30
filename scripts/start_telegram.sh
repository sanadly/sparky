#!/bin/bash
# Start the Telegram Bot

PYTHON_EXEC="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "Starting Telegram Bot..."
echo "Bot: @SparkyBerater_bot"
echo ""
"$PYTHON_EXEC" telegram_bot.py
