#!/bin/bash
DIR="/Users/mikestavrou/Desktop/ANTIGRAVITY/TRADING DASHBOARD MIKE"
cd "$DIR"

# Silently kill any existing server on the port
lsof -ti :8502 | xargs kill -9 2>/dev/null

# Start the Streamlit server in the background using the virtual environment
nohup ./venv/bin/python -m streamlit run app.py --server.port 8502 > /tmp/mikes_journal.log 2>&1 &

# Wait a brief moment for the server to spin up
sleep 3

# Open the dashboard natively in the default browser
open "http://localhost:8502"
