#!/bin/bash
# Start A2Z Nexus — Backend + Frontend

echo "Starting A2Z Nexus backend..."
cd backend
if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
if [ ! -f "../.env" ]; then
  echo "Creating .env from .env.example..."
  cp ../.env.example ../.env
fi
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 4000 &
BACKEND_PID=$!
cd ..

echo "Starting A2Z Nexus frontend..."
cd frontend
[ ! -d node_modules ] && npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "A2Z Nexus is running!"
echo "  Backend API : http://localhost:4000"
echo "  API Docs    : http://localhost:4000/docs"
echo "  Frontend    : http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop."
wait $BACKEND_PID $FRONTEND_PID
