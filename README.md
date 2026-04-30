# AI Travel Assistant 🌍✈️

![Tests](https://github.com/DarshanHari19/AI-travel-assistant/actions/workflows/main.yml/badge.svg)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/redis-7-red.svg)](https://redis.io/)
[![LangChain](https://img.shields.io/badge/🦜_LangChain-equipped-green.svg)](https://python.langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393.svg)](https://fastapi.tiangolo.com/)

A production-ready AI-powered travel assistant with real-time weather data, Redis caching, strategic airport intelligence, and intelligent travel recommendations. Built with LangChain, GPT-4, PostgreSQL, and deployed to production with full CI/CD.

## 🚀 **[Try Live Demo](https://ai-travel-assistant-6svv.vercel.app/)** ← Click to test!

**Try asking:**
- "What's the weather in Tokyo?"
- "Packing list for Paris in spring"
- "I have a 75-minute layover at JFK from Terminal 4 to Terminal 5 - is that enough time?"

**Backend API:** https://ai-travel-assistant-production.up.railway.app/health

## ✨ Features

- 🤖 **GPT-4 Powered**: Executive Travel Strategist with mandatory verification protocol
- 🌤️ **Real-time Weather**: Live weather forecasts via OpenWeatherMap API (with caching)
- ✈️ **Flight Tracking**: Real-time flight status from AeroDataBox (RapidAPI)
- 🚀 **Redis Caching**: 70% cost reduction, 70% latency improvement (30min weather, 5min flights)
- 🛫 **Airport Intelligence**: Strategic logistics RAG (JFK terminal transfers, security patterns)
- 💾 **PostgreSQL Persistence**: Conversation memory across server restarts
- 🧪 **Automated Testing**: 18 comprehensive tests with GitHub Actions CI/CD
- 🔒 **Production Security**: Rate limiting, CORS protection, API key masking
- 📊 **Multi-Source RAG**: FAISS vector store with city guides + airport logistics
- 🎨 **Modern UI**: React frontend with Tailwind CSS
- 📦 **Clean Architecture**: Proper Python packaging (pyproject.toml), no path hacks

## 🛠️ Tech Stack

**Frontend (Vercel)**
- React 18 + Vite
- Tailwind CSS for styling
- Axios for API calls

**Backend (Railway)**
- Python 3.11 + FastAPI
- LangChain + LangGraph for AI orchestration
- OpenAI GPT-4 for intelligence
- PostgreSQL (Neon) for conversation persistence
- Redis (Upstash) for caching layer
- FAISS for vector search (RAG)

**DevOps & Testing**
- GitHub Actions CI/CD with 18 automated tests
- Docker containerization
- Production monitoring & health checks
- Rate limiting & CORS security

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
└── frontend/              # React Frontend (Executive UI)
    ├── src/
    │   ├── App.jsx        # Main application component
    │   ├── components/    # React components
    │   └── index.css      # Global styles
    ├── package.json       # Node dependencies
    ├── vite.config.js     # Vite configuration
    └── README.md          # Frontend documentation
```

## � Local Development (Optional)

> **Note:** The application is already deployed and accessible at the [live demo](https://ai-travel-assistant-6svv.vercel.app/). Local setup is only needed if you want to run it yourself or contribute to the codebase.

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend)
- PostgreSQL 16+ (for conversation persistence)
- Redis 7+ (for caching)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- OpenWeatherMap API key ([Get one here](https://openweathermap.org/api))

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/DarshanHari19/AI-travel-assistant.git
cd AI-travel-assistant
```

2. **Set up PostgreSQL:**
```bash
# Using Docker (recommended)
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=travel_assistant \
  --name travel-postgres \
  postgres:16-alpine
```

Or see [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for manual setup.

**2a. Set up Redis (NEW - Production caching):**
```bash
docker run -d -p 6379:6379 --name redis-cache redis:alpine
```

This enables 70% cost reduction and latency improvement. See [QUICKSTART.md](QUICKSTART.md) for cache performance details.

3. **Install Python dependencies:**
```bash
cd backend-agent
pip install -r requirements.txt
```

Or use the automated setup script:
```bash
bash setup.sh
```

4. **Configure API keys:**

Create `.env` file in `backend-agent/` (or copy from `.env.example`):

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Weather API
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Flight API (optional - uses mock data if not set)
AERODATABOX_API_KEY=your_rapidapi_key_here

# PostgreSQL Configuration
POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/travel_assistant
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Redis Configuration (NEW - for caching)
REDIS_URL=redis://localhost:6379
```

PORT=8000
```

MCP Server - `mcp-server/.env`:
```bash
OPENWEATHER_API_KEY=your_openweather_api_key_here
REDIS_URL=redis://localhost:6379  # For caching
```

4. **Install frontend dependencies:**
```bash
cd ../frontend
npm install
```

---

## 🚀 Running the System

### Option 1: Docker (Recommended for Production)

**One-command deployment:**
```bash
# Make sure .env files are configured first!
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

**Stop services:**
```bash
docker-compose down
```

### Option 2: Manual Setup (Development)

**1. Start the backend agent:**
```bash
cd backend-agent
python agent.py
```

The API will be available at `http://localhost:8000`

**2. Start the frontend (in a new terminal):**
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 🧪 Testing

### Automated CI/CD Pipeline

Every push to `main` triggers automated testing via **GitHub Actions**:

- ✅ **18 comprehensive tests** across all components
- ✅ **PostgreSQL 16** service container for integration tests
- ✅ **Python 3.11** environment with cached dependencies
- ✅ **API keys** securely injected from GitHub Secrets
- ✅ **Status badge** shows real-time test results

**View test runs:** [GitHub Actions](https://github.com/DarshanHari19/AI-travel-assistant/actions)

### Local Testing

**Run all tests:**
```bash
# From project root
bash run_tests.sh

# Or with pytest directly
cd backend-agent
pytest -v
```

**Test categories:**
- `pytest -m unit` - Fast unit tests (no external APIs)
- `pytest -m integration` - Integration tests (requires API keys)
- `pytest -m performance` - Performance and load tests

**Production feature tests:**
```bash
cd backend-agent
python test_production_features.py
```

**Coverage report:**
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Manual Testing

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

### 3. Frontend (`frontend/`)

An executive-grade React interface for the Strategic Travel Assistant.

**Features:**
- ✅ Premium Indigo/Slate dark theme with glass morphism
- ✅ Rich markdown rendering for formatted responses
- ✅ System Reasoning accordion showing tool calls
- ✅ Visual Risk Meter (Low/Moderate/High)
- ✅ Real-time chat with auto-scroll
- ✅ Multi-city query support

**Tech Stack:**
- React 18 with Vite
- Tailwind CSS + Typography plugin
- Axios for API communication
- ReactMarkdown for response formatting

**See:** [Frontend README](frontend/README.md) for detailed setup and features

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
- [Frontend README](frontend/README.md) - React UI setup and features
- [PROMPTS.md](PROMPTS.md) - Complete development journey and prompts
- [EXECUTIVE_FEATURES.md](frontend/EXECUTIVE_FEATURES.md) - Advanced UI features guide

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

1. ✅ **Frontend Integration**: Executive-grade React UI completed
2. **Session Management**: Add persistent conversation history
3. **More Tools**: Extend with flight search, hotel booking, etc.
4. **Deployment**: Deploy to AWS/GCP/Azure with Docker
5. **Authentication**: Add user authentication and API rate limiting

## 📄 License

MIT License

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) - AI agent framework
- [OpenAI](https://openai.com/) - GPT-4 model
- [OpenWeatherMap](https://openweathermap.org/) - Weather data API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
