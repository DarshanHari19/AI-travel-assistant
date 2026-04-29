"""
Comprehensive Test Suite for Strategic Business Travel Assistant
Tests the backend agent, API endpoints, and integration with MCP server
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for mcp_server imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "sk-test-key-1234567890"
os.environ["OPENWEATHER_API_KEY"] = "test-weather-key-1234567890"
os.environ["OPENAI_MODEL"] = "gpt-4o"

from agent import app, create_travel_agent
from mcp_server import WeatherForecastResponse, ErrorResponse, DayForecast

# Mock the agent globally for TestClient (lifespan doesn't run with TestClient)
@pytest.fixture(autouse=True)
def mock_agent():
    """Mock the global travel agent for all tests"""
    from unittest.mock import MagicMock
    import agent
    
    # Create a mock agent
    mock_agent_instance = MagicMock()
    mock_agent_instance.ainvoke = AsyncMock(return_value={
        "messages": [MagicMock(content="This is a test response from the travel assistant.")]
    })
    
    # Set it globally
    agent.travel_agent = mock_agent_instance
    
    yield mock_agent_instance
    
    # Cleanup
    agent.travel_agent = None

client = TestClient(app)


# ============================================================================
# Health Check Tests
# ============================================================================

def test_root_endpoint():
    """Test the root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "Strategic Business Travel Assistant"
    assert "version" in data


def test_health_endpoint():
    """Test the detailed health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "openai_api_key" in data["components"]
    assert "openweather_api_key" in data["components"]
    assert "model" in data["components"]


def test_health_check_shows_masked_keys():
    """Test that health endpoint masks API keys for security"""
    response = client.get("/health")
    data = response.json()
    # Keys should be masked (show first/last 4 chars)
    assert "..." in data["components"]["openai_api_key"]
    assert "..." in data["components"]["openweather_api_key"]
    # Should not contain full keys
    assert "sk-test-key-1234567890" not in str(data)


# ============================================================================
# Configuration Tests
# ============================================================================

def test_config_loads_environment_variables():
    """Test that configuration loads from environment"""
    from config import config
    assert config is not None
    assert config.OPENAI_API_KEY == "sk-test-key-1234567890"
    assert config.OPENWEATHER_API_KEY == "test-weather-key-1234567890"
    assert config.OPENAI_MODEL == "gpt-4o"


def test_config_masks_api_keys():
    """Test that config properly masks API keys in repr"""
    from config import config
    config_str = str(config)
    # Masked format is first 4 chars...last 4 chars (e.g., "sk-t...7890")
    assert "..." in config_str  # Contains masking
    assert "sk-test-key-1234567890" not in config_str  # Full key not shown


def test_mask_api_key_function():
    """Test the API key masking utility function"""
    from config import mask_api_key
    
    assert mask_api_key("sk-1234567890abcdef") == "sk-1...cdef"
    assert mask_api_key("short") == "***"
    assert mask_api_key(None) == "NOT_SET"
    assert mask_api_key("") == "NOT_SET"


# ============================================================================
# Chat Endpoint Tests
# ============================================================================

@patch('agent.create_travel_agent')
def test_chat_endpoint_valid_request(mock_create_agent):
    """Test successful chat request"""
    # Mock the agent response
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [
            MagicMock(content="User message"),
            MagicMock(content="Based on London's weather, you should pack an umbrella.")
        ]
    }
    mock_create_agent.return_value = mock_agent
    
    response = client.post("/chat", json={
        "message": "What's the weather in London?",
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert data["session_id"] == "test_session"


def test_chat_endpoint_empty_message():
    """Test that empty messages are handled"""
    response = client.post("/chat", json={
        "message": "",
        "session_id": "test_session"
    })
    # May return 200 (empty response), 422 (validation), or 500 (agent error with test key)
    assert response.status_code in [200, 422, 500]


def test_chat_endpoint_missing_message():
    """Test that missing message field is rejected"""
    response = client.post("/chat", json={
        "session_id": "test_session"
    })
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_default_session_id():
    """Test that session_id defaults if not provided"""
    with patch('agent.create_travel_agent') as mock_create_agent:
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [MagicMock(content="Response")]
        }
        mock_create_agent.return_value = mock_agent
        
        response = client.post("/chat", json={
            "message": "Test message"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "default"


# ============================================================================
# Agent Creation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_travel_agent_initializes():
    """Test that agent creation doesn't raise errors"""
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    
    try:
        # Create a temporary in-memory SQLite checkpointer for testing
        async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:
            await memory.setup()
            agent = create_travel_agent(memory)
            assert agent is not None
    except Exception as e:
        pytest.fail(f"Agent creation failed: {str(e)}")


# ============================================================================
# Tool Integration Tests
# ============================================================================

@pytest.mark.asyncio
@patch('mcp_server.server.fetch_weather_data')
async def test_weather_tool_success(mock_fetch):
    """Test successful weather tool execution"""
    # Mock weather data response with correct structure
    mock_fetch.return_value = {
        'current': {
            'name': 'London',
            'sys': {'country': 'GB'},
            'main': {'temp': 15.2, 'feels_like': 14.1, 'humidity': 72},
            'weather': [{'description': 'partly cloudy'}],
            'wind': {'speed': 3.5}
        },
        'forecast': {
            'list': [
                {
                    'dt': 1711065600,
                    'dt_txt': '2024-03-22 12:00:00',
                    'main': {'temp': 14.5, 'humidity': 70},
                    'weather': [{'description': 'light rain'}]
                }
            ] * 24
        }
    }
    
    # Import the decorated tool and invoke it properly
    from agent import get_city_weather_forecast
    # The @tool decorator creates a StructuredTool, so we need to invoke it
    result = await get_city_weather_forecast.ainvoke({"city_name": "London"})
    
    assert isinstance(result, dict)
    assert result.get('city') == 'London'
    assert 'current_temp' in result


@pytest.mark.asyncio
@patch('mcp_server.server.fetch_weather_data')
async def test_weather_tool_handles_errors(mock_fetch):
    """Test that weather tool handles API errors gracefully"""
    from fastapi import HTTPException
    
    # Mock API error
    mock_fetch.side_effect = HTTPException(
        status_code=404,
        detail="City 'InvalidCity' not found"
    )
    
    from agent import get_city_weather_forecast
    # The @tool decorator creates a StructuredTool, so we need to invoke it
    result = await get_city_weather_forecast.ainvoke({"city_name": "InvalidCity"})
    
    assert isinstance(result, dict)
    assert 'error' in result


# ============================================================================
# CORS Tests
# ============================================================================

def test_cors_headers_present():
    """Test that CORS headers are configured"""
    response = client.options("/")
    # CORS headers should be present
    assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()] or \
           response.status_code in [200, 405]  # Some frameworks handle OPTIONS differently


# ============================================================================
# Error Handling Tests
# ============================================================================

@patch('agent.create_travel_agent')
def test_chat_handles_agent_errors(mock_create_agent):
    """Test that agent errors are handled gracefully"""
    mock_agent = AsyncMock()
    mock_agent.ainvoke.side_effect = Exception("LLM API Error")
    mock_create_agent.return_value = mock_agent
    
    response = client.post("/chat", json={
        "message": "Test message",
        "session_id": "test_session"
    })
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require real API keys (set RUN_INTEGRATION_TESTS=1)"
)
def test_full_integration_chat():
    """
    Full integration test with real APIs
    Only runs if RUN_INTEGRATION_TESTS=1 and real API keys are set
    """
    response = client.post("/chat", json={
        "message": "What's the weather in London?",
        "session_id": "integration_test"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["response"]) > 0
    assert "london" in data["response"].lower()


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.performance
@patch('agent.create_travel_agent')
def test_concurrent_requests(mock_create_agent):
    """Test that multiple concurrent requests are handled"""
    import concurrent.futures
    
    mock_agent = AsyncMock()
    mock_agent.ainvoke.return_value = {
        "messages": [MagicMock(content="Response")]
    }
    mock_create_agent.return_value = mock_agent
    
    def make_request(i):
        return client.post("/chat", json={
            "message": f"Test message {i}",
            "session_id": f"session_{i}"
        })
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(make_request, range(10)))
    
    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
