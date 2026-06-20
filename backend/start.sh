#!/bin/bash
set -e

echo "=== Starting Museum AI Backend ==="

# Start LiveKit Agent in background
echo ">>> Starting LiveKit Agent..."
python app/agent.py start &
AGENT_PID=$!
echo "LiveKit Agent PID: $AGENT_PID"

# Start FastAPI
echo ">>> Starting FastAPI on port 7860..."
uvicorn main:app --host 0.0.0.0 --port 7860 &
API_PID=$!
echo "FastAPI PID: $API_PID"

# Wait for the API process to keep container running
wait $API_PID
