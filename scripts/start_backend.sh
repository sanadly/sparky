#!/bin/bash
# Start the FastAPI Backend with Web Portal

PYTHON_EXEC="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "Starting INTENSE Energieberater Backend..."
echo "Web Portal: http://localhost:8000"
echo "API: http://localhost:8000/api/chat"
echo ""
"$PYTHON_EXEC" -m backend.main
