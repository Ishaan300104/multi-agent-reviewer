#!/bin/bash

# Start All MCP Servers for Research Paper Reviewer
# Usage: ./start_servers.sh [--dev]

set -e

echo "=========================================="
echo "  Multi-Agent Paper Reviewer Startup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if virtual environment exists
# if [ ! -d "venv" ]; then
#     echo -e "${YELLOW}⚠ Virtual environment not found. Creating...${NC}"
#     python3 -m venv venv
#     source venv/bin/activate
#     pip install --upgrade pip
#     pip install -r requirements.txt
#     echo -e "${GREEN}✓ Virtual environment created${NC}"
# else
#     source venv/bin/activate
#     echo -e "${GREEN}✓ Virtual environment activated${NC}"
# fi

# Create necessary directories
mkdir -p data/sample_papers
mkdir -p data/processed
mkdir -p data/cache
mkdir -p eval/results
mkdir -p logs

echo -e "${GREEN}✓ Directories created${NC}"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${YELLOW}⚠ .env file not found. Using defaults${NC}"
fi

# Function to start server in background
start_server() {
    local name=$1
    local script=$2
    local port=$3
    
    echo -e "${YELLOW}Starting $name on port $port...${NC}"
    # python $script > logs/${name}.log 2>&1 &                  # added "-m" to run it as a module
    python -m $script > logs/${name}.log 2>&1 &
    local pid=$!
    echo $pid > logs/${name}.pid
    
    # Wait a moment and check if process is still running
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✓ $name started (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ $name failed to start${NC}"
        cat logs/${name}.log
        return 1
    fi
}

# Start all MCP servers
echo ""
echo "Starting MCP Servers..."
echo "---"

# start_server "ReaderAgent" "mcp-server/reader_server.py" 5001                 Original code, I modified syntax
# start_server "CriticAgent" "mcp-server/critic_server.py" 5002
# start_server "MetaReviewerAgent" "mcp-server/meta_reviewer_server.py" 5003
# start_server "CiteAgent" "mcp-server/cite_server.py" 5004

start_server "ReaderAgent" "mcp_server.reader_server" 5001
start_server "CriticAgent" "mcp_server.critic_server" 5002
start_server "MetaReviewerAgent" "mcp_server.meta_reviewer_server" 5003
start_server "CiteAgent" "mcp_server.cite_server" 5004

echo ""
echo -e "${GREEN}✓ All MCP servers started${NC}"
echo ""

# Wait for servers to be ready
echo "Waiting for servers to be ready..."
sleep 5

# Check server health
echo ""
echo "Checking server health..."
for port in 5001 5002 5003 5004; do
    if curl -s http://localhost:$port/health > /dev/null; then
        echo -e "${GREEN}✓ Port $port: Healthy${NC}"
    else
        echo -e "${RED}✗ Port $port: Not responding${NC}"
    fi
done

echo ""
echo "=========================================="
echo "  All Services Started Successfully!"
echo "=========================================="
echo ""
echo "MCP Servers:"
echo "  - Reader Agent:      http://localhost:5001"
echo "  - Critic Agent:      http://localhost:5002"
echo "  - MetaReviewer:      http://localhost:5003"
echo "  - CiteAgent:         http://localhost:5004"
echo ""
echo "To start the UI, run:"
echo "  streamlit run ui/streamlit_app.py"
echo ""
echo "To stop all servers, run:"
echo "  ./scripts/stop_servers.sh"
echo ""
echo "Logs are available in: logs/"
echo "=========================================="