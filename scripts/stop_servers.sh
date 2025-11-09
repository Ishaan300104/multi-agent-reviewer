#!/bin/bash

# Stop All MCP Servers

echo "Stopping all MCP servers..."

# Array of server names
servers=("ReaderAgent" "CriticAgent" "MetaReviewerAgent" "CiteAgent")

for server in "${servers[@]}"; do
    pidfile="logs/${server}.pid"
    
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $server (PID: $pid)..."
            kill $pid
            rm "$pidfile"
            echo "✓ $server stopped"
        else
            echo "⚠ $server (PID: $pid) not running"
            rm "$pidfile"
        fi
    else
        echo "⚠ No PID file found for $server"
    fi
done

# Also kill any Python processes on the MCP ports
echo ""
echo "Cleaning up any remaining processes on MCP ports..."
for port in 5001 5002 5003 5004; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)"
        kill $pid 2>/dev/null || true
    fi
done

echo ""
echo "All servers stopped."