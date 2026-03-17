# System Architecture

## Complete Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                 │
│  "I'm flying to London tomorrow. Should I worry about delays?"           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     │ HTTP POST /chat
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  BACKEND AGENT (agent.py)                                │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  FastAPI Endpoint: /chat                                    │        │
│  │  - Receives user message                                    │        │
│  │  - Creates agent executor                                   │        │
│  │  - Invokes agent with input                                 │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
│                         ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  LangChain Agent (OpenAI Functions Agent)                   │        │
│  │                                                              │        │
│  │  1. Receives: "I'm flying to London..."                     │        │
│  │  2. System Prompt: Strategic Business Travel Assistant      │        │
│  │  3. Available Tools: [get_city_weather_forecast]            │        │
│  │  4. Reasoning: "I need weather data for London"             │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
│                         ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  Tool Execution: @tool decorator                            │        │
│  │  get_city_weather_forecast("London")                        │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │
                          │ Function Call
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  MCP SERVER (server.py)                                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  MCP Tool: get_weather_forecast(city_name="London")         │        │
│  │  - Validates input                                          │        │
│  │  - Prepares API requests                                    │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
│                         ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  API Call: fetch_weather_data()                             │        │
│  │  - Current weather: /weather?q=London                       │        │
│  │  - Forecast: /forecast?q=London                             │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │
                          │ HTTP GET
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              OPENWEATHERMAP REST API                                     │
│                                                                           │
│  Current Weather:                                                        │
│  GET https://api.openweathermap.org/data/2.5/weather                    │
│      ?q=London&appid=YOUR_KEY&units=metric                              │
│                                                                           │
│  Returns: temp, feels_like, humidity, conditions, wind_speed            │
│                                                                           │
│  5-Day Forecast:                                                         │
│  GET https://api.openweathermap.org/data/2.5/forecast                   │
│      ?q=London&appid=YOUR_KEY&units=metric                              │
│                                                                           │
│  Returns: 40 data points (5 days × 8 times/day)                         │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           │ JSON Response
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  MCP SERVER (Processing)                                 │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  process_forecast_data()                                    │        │
│  │  - Aggregate 40 data points into daily summaries            │        │
│  │  - Extract min/max temps for each day                       │        │
│  │  - Determine dominant weather conditions                    │        │
│  │  - Calculate average humidity                               │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
│                         ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  Create Pydantic Model: WeatherForecastResponse             │        │
│  │  {                                                           │        │
│  │    "city": "London",                                         │        │
│  │    "country": "GB",                                          │        │
│  │    "current_temp": 15.2,                                     │        │
│  │    "current_conditions": "partly cloudy",                    │        │
│  │    "feels_like": 14.1,                                       │        │
│  │    "humidity": 72,                                           │        │
│  │    "wind_speed": 3.5,                                        │        │
│  │    "three_day_outlook": [                                    │        │
│  │      {date: "2026-03-16", temp_min: 12, temp_max: 18, ...}, │        │
│  │      {date: "2026-03-17", temp_min: 13, temp_max: 19, ...}, │        │
│  │      {date: "2026-03-18", temp_min: 14, temp_max: 20, ...}  │        │
│  │    ]                                                         │        │
│  │  }                                                           │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │
                          │ Return Pydantic Model
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  LANGCHAIN TOOL (Conversion)                             │
│                                                                           │
│  @tool converts Pydantic model to dict:                                 │
│  result.model_dump() → JSON-serializable dict                           │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           │ Tool Output (dict)
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  LANGCHAIN AGENT (Analysis)                              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │  GPT-4 Model (ChatOpenAI)                                   │        │
│  │                                                              │        │
│  │  Context:                                                    │        │
│  │  - System Prompt: Strategic Business Travel Assistant       │        │
│  │  - User Query: "I'm flying to London tomorrow..."           │        │
│  │  - Tool Output: {weather data for London}                   │        │
│  │                                                              │        │
│  │  Analysis:                                                   │        │
│  │  - Current temp: 15°C (moderate)                            │        │
│  │  - Conditions: partly cloudy (good visibility)              │        │
│  │  - Wind: 3.5 m/s (low - unlikely to cause delays)           │        │
│  │  - 3-day outlook: stable conditions                         │        │
│  │                                                              │        │
│  │  Generates Response:                                         │        │
│  │  "Based on London's weather forecast, flight delays are     │        │
│  │   unlikely. Current conditions show partly cloudy skies     │        │
│  │   with moderate temperatures and low wind speeds..."        │        │
│  └──────────────────────┬──────────────────────────────────────┘        │
│                         │                                                │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │
                          │ Agent Output
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  FASTAPI ENDPOINT (Response)                             │
│                                                                           │
│  ChatResponse(                                                           │
│    response="Based on London's weather forecast...",                    │
│    session_id="user_123"                                                │
│  )                                                                       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           │ HTTP 200 OK
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
│  Receives detailed travel advice with weather-based recommendations     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌────────────────────────────────────────────────────────┐
│  Potential Error Points                                │
└────────────────────────────────────────────────────────┘

1. Invalid City Name
   ├─ User: "Weather in XYZ123"
   ├─ OpenWeatherMap: 404 Not Found
   ├─ MCP Server: Catches 404
   ├─ Returns: ErrorResponse(error="City not found...", status_code=404)
   ├─ Agent: Receives error, explains to user
   └─ User: "The city 'XYZ123' was not found. Please check spelling."

2. Invalid API Key
   ├─ OpenWeatherMap: 401 Unauthorized
   ├─ MCP Server: Catches 401
   ├─ Returns: ErrorResponse(error="Invalid API key...", status_code=401)
   ├─ Agent: Receives error
   └─ User: "Unable to fetch weather data. API key issue."

3. Network Error
   ├─ Connection timeout or network issue
   ├─ MCP Server: Catches httpx.RequestError
   ├─ Returns: ErrorResponse(error="Network error...", status_code=503)
   └─ User: "Unable to reach weather service at the moment."
```

## Component Responsibilities

```
┌──────────────────────────────────────────────────────────────┐
│  Component          │  Responsibilities                      │
├─────────────────────┼────────────────────────────────────────┤
│  MCP Server         │  - Weather data fetching               │
│  (server.py)        │  - API error handling                  │
│                     │  - Data aggregation                    │
│                     │  - Pydantic validation                 │
│                     │  - JSON response formatting            │
│                     │                                        │
│  LangChain Tool     │  - Function signature definition       │
│  (@tool)            │  - Type conversion (Pydantic → dict)  │
│                     │  - Tool description for LLM           │
│                     │                                        │
│  LangChain Agent    │  - Natural language understanding      │
│  (GPT-4)            │  - Tool selection and invocation       │
│                     │  - Weather data analysis              │
│                     │  - Travel advice generation           │
│                     │  - Response formatting                │
│                     │                                        │
│  FastAPI Backend    │  - HTTP request handling              │
│  (agent.py)         │  - Agent lifecycle management         │
│                     │  - Response serialization             │
│                     │  - Health monitoring                  │
└──────────────────────────────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Layer              │  Technology                           │
├─────────────────────┼───────────────────────────────────────┤
│  AI Model           │  OpenAI GPT-4o                        │
│  Agent Framework    │  LangChain (OpenAI Functions Agent)   │
│  Web Framework      │  FastAPI                              │
│  Data Validation    │  Pydantic v2                          │
│  HTTP Client        │  httpx (async)                        │
│  MCP Framework      │  FastMCP                              │
│  External API       │  OpenWeatherMap REST API              │
│  Environment        │  Python 3.10+                         │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

1. **Microservice Architecture**: MCP server as independent weather service
2. **Tool Abstraction**: LangChain tool wrapper for modular integration
3. **Type Safety**: Pydantic models throughout the stack
4. **Async/Await**: Full async support for concurrent operations
5. **Error Boundaries**: Graceful error handling at each layer
6. **Separation of Concerns**: Clear responsibility boundaries
7. **API-First Design**: RESTful endpoints with OpenAPI docs

---

This architecture demonstrates production-ready patterns for building
AI agents with external data sources!
