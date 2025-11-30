#!/bin/bash

# Path to the python executable that has the dependencies installed
PYTHON_EXEC="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "Running Setup Test..."
echo "Running Setup Test..."
"$PYTHON_EXEC" tests/test_setup.py

echo "Running Flow Test..."
"$PYTHON_EXEC" tests/test_flow.py

echo "All tests passed!"
echo ""
echo "To start the backend, run:"
echo "$PYTHON_EXEC -m backend.main"
echo ""
echo "To start the Telegram bot, run:"
echo "$PYTHON_EXEC backend/telegram_bot.py"
