#!/usr/bin/env bash
# Autonomous AI Software Development Factory Startup Script
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=========================================================="
echo " Starting Autonomous AI Software Development Factory"
echo "=========================================================="

# Check and activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run database table initialization
python -c "import asyncio; from factory.core.database import init_db; asyncio.run(init_db())"

echo "Starting FastAPI Orchestrator Backend on http://127.0.0.1:8000..."
uvicorn factory.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Next.js Management Dashboard on http://localhost:3000..."
cd "$DIR/dashboard"
npm run dev -- -p 3000 &
FRONTEND_PID=$!

echo "Factory is running!"
echo "• Dashboard URL: http://localhost:3000"
echo "• API Docs URL:  http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to terminate both services."

cleanup() {
    echo "Shutting down Factory services..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
