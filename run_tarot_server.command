#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Tarot image server..."
echo "Open http://localhost:8765 in Chrome when ready."
python3 img_server_local.py
