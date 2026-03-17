# Strategic Business Travel Assistant - Backend Agent

A LangChain-powered AI agent that provides intelligent travel advice using real-time weather data from the OpenWeatherMap API. The agent analyzes weather forecasts to help travelers make informed decisions about flight delays, packing, and travel timing.

## Features

- 🤖 **LangChain Agent**: Built with LangGraph's `create_react_agent` (2026 standard) and OpenAI GPT-4
- 🌦️ **Weather Intelligence**: Integrates with OpenWeatherMap MCP server for real-time data
- ✈️ **Travel Advice**: Provides insights on flight delays, packing recommendations, and optimal travel times
- 🚀 **FastAPI Backend**: RESTful API with `/chat` endpoint for easy integration
- 📝 **Structured Responses**: Type-safe with Pydantic models

## Architecture

```
User Request → FastAPI /chat → LangChain Agent → Weather Tool → OpenWeatherMap API
                                      ↓
                              GPT-4 Analysis
                                      ↓
                           Travel Advice Response
```

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key
- OpenWeatherMap API key

### Setup

1. **Install dependencies:**
```bash
cd backend-agent
pip install -r requirements.txt
```

2. **Install MCP server dependencies:**
```bash
cd ../mcp-server
pip install -r requirements.txt
cd ../backend-agent
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENWEATHER_API_KEY` - Your OpenWeatherMap API key
- `OPENAI_MODEL` - Model to use (default: gpt-4o)
- `PORT` - Server port (default: 8000)

## Usage

### Starting the Server

```bash
python agent.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### POST /chat

Send a message to the Strategic Business Travel Assistant.

**Request:**
```json
{
  "message": "I'm traveling to London next week. What should I expect weather-wise?",
  "session_id": "user_123"
}
```

**Response:**
```json
{
  "response": "I'll check the current weather forecast for London...\n\nBased on the current forecast for London:\n- Current temperature: 15.2°C with partly cloudy conditions\n- 3-day outlook shows temperatures ranging from 12-20°C with mixed conditions\n\nTravel Recommendations:\n1. Pack layers - temperatures vary throughout the day\n2. Bring an umbrella - light rain expected on Day 1\n3. Flight delays unlikely - no severe weather predicted\n4. Best travel time: Day 2-3 when conditions improve\n\nHave a great trip!",
  "session_id": "user_123"
}
```

#### GET /health

Check the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "openai_api_key": "configured",
    "openweather_api_key": "configured",
    "model": "gpt-4o"
  }
}
```

### Example Queries

```bash
# Basic weather inquiry
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What's the weather like in Tokyo?"}'

# Travel planning
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I'm flying to Paris tomorrow. Should I be concerned about delays?"}'

# Packing advice
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I pack for a 3-day trip to New York?"}'
```

## Agent Architecture

### 1. Chat Model Initialization

Uses `langchain_openai.ChatOpenAI` with GPT-4:
```python
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)
```

### 2. LangChain Tool

The `get_weather_forecast` function is converted to a LangChain tool using the `@tool` decorator:
```python
@tool
async def get_city_weather_forecast(city_name: str) -> dict:
    """Get current weather and 3-day forecast for a specified city."""
    result = await get_weather_forecast(city_name)
    return result.model_dump()
```

### 3. Agent Creation

Uses LangGraph's modern `create_react_agent` (2026 standard):
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

agent = create_react_agent(
    llm,
    tools=[get_city_weather_forecast],
    prompt=SystemMessage(content=SYSTEM_PROMPT)
)
```

### 4. System Prompt

The agent is configured as a **Strategic Business Travel Assistant** with expertise in:
- Predicting flight delays based on weather patterns
- Providing packing recommendations
- Advising on optimal travel times
- Warning about weather-related risks

### 5. FastAPI Integration

The `/chat` endpoint:
- Accepts user messages via POST request
- Creates and executes the agent
- Returns structured responses
- Handles errors gracefully

## Development

### Project Structure

```
backend-agent/
├── agent.py           # Main agent implementation
├── requirements.txt   # Python dependencies
├── .env.example       # Example environment configuration
└── README.md          # This file
```

### Testing

```bash
# Run tests
pytest

# Test with curl
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about weather in Seattle"}'
```

### Logging

The agent uses Python's logging module. Set log level via environment:
```bash
export LOG_LEVEL=DEBUG
python agent.py
```

## Integration with Frontend

To connect with a frontend application:

1. **CORS Configuration** (add to agent.py):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Frontend Example** (JavaScript):
```javascript
async function askAgent(message) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  const data = await response.json();
  return data.response;
}
```

## Troubleshooting

### Common Issues

**"OPENAI_API_KEY not set"**
- Ensure your `.env` file contains a valid OpenAI API key
- Check that python-dotenv is loading the file correctly

**"Invalid API key" (401 from OpenWeatherMap)**
- Verify your OpenWeatherMap API key in `.env`
- Ensure the key is activated (can take a few hours after signup)

**Agent not using the weather tool**
- Check that the system prompt clearly instructs tool usage
- Verify the tool description is detailed and relevant

**Import errors for mcp-server**
- Ensure mcp-server dependencies are installed
- Check that sys.path includes the parent directory

## License

MIT License

## Support

For issues or questions:
- LangChain Documentation: https://python.langchain.com/
- OpenAI API Documentation: https://platform.openai.com/docs
- FastAPI Documentation: https://fastapi.tiangolo.com/
