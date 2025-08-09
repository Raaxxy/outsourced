#!/bin/bash

# VA Document Classification System - Development Startup Script

echo "🚀 Starting VA Document Classification System Development Environment"
echo "=================================================="

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n🛑 Shutting down development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "📡 Starting FastAPI backend server..."
cd backend
source ../venv/bin/activate
python start.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "🎨 Starting React frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Development servers started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "📡 Backend:  http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "🔄 Press Ctrl+C to stop all servers"
echo "=================================================="

# Wait for background processes
wait 