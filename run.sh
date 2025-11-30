#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CBI System (Backend + Frontend + Bot)...${NC}"

# Function to kill process on a specific port
kill_port() {
    PORT=$1
    PID=$(lsof -ti :$PORT)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}⚠️  Killing process on port $PORT (PID: $PID)...${NC}"
        kill -9 $PID
    fi
}

# Cleanup function
cleanup() {
    echo -e "\n${RED}🛑 Shutting down all services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# 1. Clean up ports
echo -e "${YELLOW}🧹 Cleaning up ports 8000 and 3000...${NC}"
kill_port 8000
kill_port 3000

# 2. Check for venv
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found! Please run setup first.${NC}"
    exit 1
fi

PYTHON_EXEC="./venv/bin/python"

# 3. Start Backend
echo -e "${GREEN}🔹 Starting Backend Server...${NC}"
$PYTHON_EXEC -m backend.main > backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"

# 4. Start Telegram Bot
echo -e "${GREEN}🔹 Starting Telegram Bot...${NC}"
$PYTHON_EXEC -m backend.telegram_bot > bot.log 2>&1 &
BOT_PID=$!
echo "   PID: $BOT_PID"

# 5. Start Frontend
echo -e "${GREEN}🔹 Starting Frontend...${NC}"
cd web-portal
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ All services started!${NC}"
echo -e "   Backend:  http://localhost:8000"
echo -e "   Frontend: http://localhost:3000"
echo -e "   Logs:     backend.log, bot.log"
echo -e "${YELLOW}Press Ctrl+C to stop everything.${NC}"

wait
