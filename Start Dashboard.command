#!/bin/bash
# Move to the directory where this script is located
cd "$(dirname "$0")"

echo "=========================================="
echo "    Starting Mikes Trading Journal...     "
echo "=========================================="
echo ""
echo "⚠️  PLEASE KEEP THIS TERMINAL WINDOW OPEN ⚠️"
echo "   (The app will close if you close this)   "
echo ""

# Kill any existing streamlit instances on port 8502
lsof -ti :8502 | xargs kill -9 2>/dev/null

# Start the server in the background
./venv/bin/python -m streamlit run app.py --server.port 8502 > /tmp/mikes_journal.log 2>&1 &
STR_PID=$!

echo "Server started. Waiting for it to boot up..."
sleep 3

echo "Opening in your browser..."
# Just open the URL normally using the system default browser
open "http://localhost:8502"

echo ""
echo "Dashboard is running!"
echo "To shut down, press Control+C in this window or just close this window."
echo "=========================================="

# Keep the script alive by tailing the log file. If the user hits Ctrl+C, the trap underneath handles cleanup.
# We set up a trap to naturally catch the script exiting
trap 'echo ""; echo "Shutting down the background server..."; kill -9 $STR_PID 2>/dev/null; lsof -ti :8502 | xargs kill -9 2>/dev/null; echo "Server shut down successfully. Goodbye!"; exit 0' EXIT INT TERM

# Wait forever until killed.
tail -f /tmp/mikes_journal.log
