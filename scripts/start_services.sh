#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Path to the python executable that has the dependencies installed
PYTHON_EXEC="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

echo "🚀 Starting CBI Services..."

# 1. Start Backend
echo "🔹 Starting Backend Server..."
"$PYTHON_EXEC" -m backend.main > backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend running (PID: $BACKEND_PID)"

# 2. Start Telegram Bot
echo "🔹 Starting Telegram Bot..."
"$PYTHON_EXEC" -m backend.telegram_bot > bot.log 2>&1 &
BOT_PID=$!
echo "   ✅ Bot running (PID: $BOT_PID)"

# 3. Start Frontend
echo "🔹 Starting Frontend..."
cd web-portal
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 All services started!"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:5173"
echo "   - Bot: Active"
echo ""
echo "PRESS CTRL+C TO STOP ALL SERVICES"
echo ""

# Wait for any process to exit
wait
