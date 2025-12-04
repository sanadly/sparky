#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting CBI System in PRODUCTION Mode...${NC}"

# Check for venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found! Please run setup first."
    exit 1
fi

# Activate venv
source venv/bin/activate

# Install Gunicorn if not present
if ! pip show gunicorn > /dev/null; then
    echo "📦 Installing Gunicorn..."
    pip install gunicorn
fi

# Start Gunicorn
echo -e "${GREEN}🔹 Starting Backend with Gunicorn...${NC}"
gunicorn -c gunicorn_conf.py backend.main:app
