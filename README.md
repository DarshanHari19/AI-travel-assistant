# InMarket AI Builder Challenge

A complete AI-powered travel assistant system using Model Context Protocol (MCP), LangChain, and OpenWeatherMap API.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Request                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Agent (LangChain + FastAPI)            │
│  - GPT-4 powered Strategic Business Travel Assistant        │
│  - Analyzes travel queries                                  │
│  - Calls weather tools as needed                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               MCP Server (Weather Tool)                     │
│  - get_weather_forecast function                            │
│  - Pydantic models for type safety                          │
│  - Error handling (401, 404)                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenWeatherMap REST API                        │
│  - Current weather data                                     │
│  - 5-day/3-hour forecast                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
inmarket-ai-builder-challenge/
├── backend-agent/          # LangChain AI Agent
│   ├── agent.py           # Main agent with FastAPI
│   ├── test_agent.py      # Testing utilities
│   ├── setup.sh           # Setup script
│   ├── requirements.txt   # Dependencies
│   └── README.md          # Documentation
├── mcp-server/            # MCP Weather Server
│   ├── server.py          # MCP server implementation
│   ├── requirements.txt   # Dependencies
│   └── README.md          # Documentation
└── frontend/              # Frontend (placeholder)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- OpenWeatherMap API key ([Get one here](https://openweathermap.org/api))

### Installation

1. **Clone and navigate to the project:**
```bash
cd backend-agent
```

2. **Run the setup script:**
```bash
./setup.sh
```

3. **Configure API keys:**
Edit `backend-agent/.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
OPENAI_MODEL=gpt-4o
```

### Running the System

**Start the backend agent:**
```bash
cd backend-agent
python agent.py
```

The API will be available at `http://localhost:8000`

### Testing

**Run automated tests:**
```bash
cd backend-agent
python test_agent.py
```

**Interactive mode:**
```bash
python test_agent.py --mode interactive
```

**Single query:**
```bash
python test_agent.py --message "What's the weather in Paris?"
```

**Using curl:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I'm traveling to London tomorrow. What should I expect?"}'
```

## 🔧 Components

### 1. MCP Server (`mcp-server/`)

A microservice wrapper for the OpenWeatherMap REST API implementing MCP standards.

**Features:**
- ✅ `get_weather_forecast` tool with `city_name` parameter
- ✅ Graceful error handling (401, 404)
- ✅ Pydantic models for structured responses
- ✅ 3-day weather outlook with temperature ranges

**Response Schema:**
```json
{
  "city": "London",
  "country": "GB",
  "current_temp": 15.2,
  "current_conditions": "partly cloudy",
  "three_day_outlook": [...]
}
```

### 2. Backend Agent (`backend-agent/`)

A LangChain-powered AI agent that acts as a Strategic Business Travel Assistant.

**Features:**
- ✅ Uses `langchain_openai.ChatOpenAI` (GPT-4)
- ✅ LangChain tool conversion with `@tool` decorator
- ✅ LangGraph's `create_react_agent` (modern 2026 standard)
- ✅ Custom system prompt for travel expertise
- ✅ FastAPI `/chat` endpoint

**Capabilities:**
- Predicts flight delays based on weather
- Provides packing recommendations
- Advises on optimal travel timing
- Warns about weather-related risks

## 📚 API Documentation

### POST /chat

**Request:**
```json
{
  "message": "I'm flying to Tokyo next week. Should I worry about delays?",
  "session_id": "optional_session_id"
}
```

**Response:**
```json
{
  "response": "Let me check the weather forecast for Tokyo...\n\n[Agent's detailed response with weather analysis and travel advice]",
  "session_id": "optional_session_id"
}
```

### GET /health

Check service health and configuration status.

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

## 🧪 Example Interactions

### Example 1: Weather Check
**User:** "What's the weather like in Seattle?"

**Agent:** "I'll check the current weather forecast for Seattle... Currently 12°C with light rain. Expect similar conditions over the next 3 days with temperatures between 10-15°C. Perfect excuse to explore Pike Place Market indoors!"

### Example 2: Flight Delay Prediction
**User:** "I'm flying to Chicago tomorrow. Should I be concerned about delays?"

**Agent:** "Let me analyze the weather conditions for Chicago... Current forecast shows clear skies with no precipitation. Wind speeds are moderate at 4 m/s. Flight delays are unlikely based on current weather patterns. You should have smooth sailing!"

### Example 3: Packing Advice
**User:** "What should I pack for a 3-day trip to London?"

**Agent:** "Based on London's forecast: temperatures 12-18°C with intermittent rain... Pack: waterproof jacket, umbrella, layers (sweater/light jacket), comfortable walking shoes (waterproof recommended), and an extra pair of socks!"

## 🛠️ Development

### Manual Setup (without setup.sh)

**MCP Server:**
```bash
cd mcp-server
pip install -r requirements.txt
cp .env.example .env
# Edit .env with OPENWEATHER_API_KEY
```

**Backend Agent:**
```bash
cd backend-agent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with OPENAI_API_KEY and OPENWEATHER_API_KEY
python agent.py
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | Yes |
| `OPENAI_MODEL` | Model to use (default: gpt-4o) | No |
| `PORT` | Server port (default: 8000) | No |

## 📖 Documentation

- [Backend Agent README](backend-agent/README.md) - Detailed agent documentation
- [MCP Server README](mcp-server/README.md) - Weather server documentation

## 🔍 Troubleshooting

### "OPENAI_API_KEY not set"
- Ensure `.env` file exists in `backend-agent/`
- Verify the API key is valid and not expired

### "Invalid API key" (401 from OpenWeatherMap)
- Check that your OpenWeatherMap API key is activated
- New keys can take 1-2 hours to become active

### "City not found" (404)
- Verify city name spelling
- Try adding country code: "London,GB"

### Import errors
- Ensure both `mcp-server` and `backend-agent` dependencies are installed
- Check Python version (3.10+ required)

## 🎯 Next Steps

1. **Frontend Integration**: Create a React/Vue frontend in the `frontend/` directory
2. **Session Management**: Add conversation history and context
3. **More Tools**: Extend with flight search, hotel booking, etc.
4. **Deployment**: Deploy to AWS/GCP/Azure with Docker

## 📄 License

MIT License

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) - AI agent framework
- [OpenAI](https://openai.com/) - GPT-4 model
- [OpenWeatherMap](https://openweathermap.org/) - Weather data API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
