#!/bin/bash

# Setup script for Strategic Business Travel Assistant
# This script sets up both the MCP server and the backend agent

set -e

echo "=================================================="
echo "Strategic Business Travel Assistant - Setup"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Setup MCP Server
echo "Setting up MCP Server..."
cd ../mcp-server
echo "  - Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
if [ ! -f .env ]; then
    echo "  - Creating .env file from template..."
    cp .env.example .env
    echo "  ⚠️  Please edit mcp-server/.env and add your OPENWEATHER_API_KEY"
else
    echo "  ✓ .env file already exists"
fi
cd ../backend-agent
echo "✓ MCP Server setup complete"
echo ""

# Setup Backend Agent
echo "Setting up Backend Agent..."
echo "  - Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
if [ ! -f .env ]; then
    echo "  - Creating .env file from template..."
    cp .env.example .env
    echo "  ⚠️  Please edit backend-agent/.env and add your API keys"
else
    echo "  ✓ .env file already exists"
fi
echo "✓ Backend Agent setup complete"
echo ""

# Final instructions
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API keys:"
echo "   - Edit backend-agent/.env and add:"
echo "     • OPENAI_API_KEY"
echo "     • OPENWEATHER_API_KEY"
echo ""
echo "2. Start the backend agent:"
echo "   cd backend-agent"
echo "   python agent.py"
echo ""
echo "3. Test the agent (in a new terminal):"
echo "   cd backend-agent"
echo "   python test_agent.py"
echo ""
echo "   Or for interactive mode:"
echo "   python test_agent.py --mode interactive"
echo ""
echo "4. API will be available at:"
echo "   http://localhost:8000"
echo ""
echo "=================================================="
echo ""

# Check if .env files have been configured
if grep -q "your_openai_api_key_here" .env 2>/dev/null; then
    echo "⚠️  WARNING: Please configure your API keys in .env files before running!"
fi
