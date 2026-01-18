#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Define the port
PORT=2052

# Kill any existing process on this port
lsof -ti:$PORT | xargs kill -9 2>/dev/null

echo "=================================================="
echo "   正在更新全景照片資料庫..."
python3 scan_photos.py
echo "=================================================="
echo "   正在啟動 日光富御 全景地圖系統..."
echo "   伺服器位置: http://localhost:$PORT"
echo "=================================================="

# Function to open the browser
(sleep 1 && open "http://localhost:$PORT/index.html") &

# Start the Python HTTP server
python3 -m http.server $PORT
