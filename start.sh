#!/bin/bash
cd backend
nohup python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
cd ../frontend
npm install
npm start
kill $BACKEND_PID