#!/bin/bash
# Test runner script for Strategic Business Travel Assistant

set -e

echo "=================================================="
echo "Strategic Business Travel Assistant - Test Suite"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${RED}Error: pytest not installed${NC}"
    echo "Installing test dependencies..."
    python3 -m pip install pytest pytest-asyncio pytest-cov pytest-mock
fi

echo -e "${YELLOW}Running tests...${NC}"
echo ""

# Run backend agent tests
echo "📦 Testing Backend Agent..."
cd backend-agent
python3 -m pytest test_comprehensive.py -v --tb=short -m "not integration and not performance"
BACKEND_EXIT=$?

# Run MCP server tests
echo ""
echo "🌐 Testing MCP Server..."
cd ../mcp-server
python3 -m pytest test_comprehensive.py -v --tb=short -m "not integration"
MCP_EXIT=$?

cd ..

echo ""
echo "=================================================="

# Check results
if [ $BACKEND_EXIT -eq 0 ] && [ $MCP_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "To run integration tests (requires real API keys):"
    echo "  export RUN_INTEGRATION_TESTS=1"
    echo "  pytest -m integration"
    echo ""
    echo "To run with coverage:"
    echo "  pytest --cov=. --cov-report=html"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
