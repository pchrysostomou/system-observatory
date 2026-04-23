#!/bin/bash
# Claude Power Dashboard — Startup Script

cd "$(dirname "$0")"

echo "🚀 Starting Claude Power Dashboard..."
echo "📊 Open http://localhost:5000 in your browser"
echo "⌨️  Press Ctrl+C to stop"
echo ""

python3 app.py
