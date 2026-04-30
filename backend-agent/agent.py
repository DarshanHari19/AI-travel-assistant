#!/usr/bin/env python3
"""
LangChain Backend Agent - Executive Travel Strategist
Integrates real-time APIs, RAG intelligence, and PostgreSQL persistence
Production-ready with Redis caching and proper package structure
"""

import os
import logging
from typing import Annotated
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import secure configuration
from config import config, mask_api_key

# Import MCP server tools using proper package structure
import sys
from pathlib import Path

# Add parent directory to path to import mcp_server as package
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from mcp_server import get_weather_forecast, get_flight_status, WeatherForecastResponse, FlightStatusResponse, ErrorResponse

# Import RAG retriever with updated function name
from retriever import initialize_vector_store, query_travel_knowledge

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL if config else "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
if not config:
    logger.critical("Configuration failed to load. Check your .env file.")
    raise RuntimeError("Failed to load configuration. See logs for details.")

# Global agent instance, memory, and connection pool
travel_agent = None
memory = None
pool = None
checkpointer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown"""
    global memory, travel_agent, pool, checkpointer
    
    # Startup: Initialize PostgreSQL connection pool and checkpointer
    postgres_host = config.POSTGRES_URI.split('@')[1] if '@' in config.POSTGRES_URI else "localhost"
    logger.info(f"Connecting to PostgreSQL: {postgres_host}")
    
    # Create async connection pool
    pool = AsyncConnectionPool(
        conninfo=config.POSTGRES_URI,
        min_size=1,
        max_size=config.POSTGRES_POOL_SIZE,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    
    # Open the pool
    await pool.open()
    logger.info(f"PostgreSQL connection pool initialized (size: {config.POSTGRES_POOL_SIZE})")
    
    # Initialize PostgreSQL checkpointer - properly enter context manager
    checkpointer = AsyncPostgresSaver.from_conn_string(config.POSTGRES_URI)
    memory = await checkpointer.__aenter__()
    
    # Setup database schema (creates tables if they don't exist)
    await memory.setup()
    logger.info("AsyncPostgresSaver initialized for conversation checkpointing")
    
    # Initialize RAG vector store (CRITICAL: must succeed or searches will fail)
    try:
        vector_store = initialize_vector_store(api_key=config.OPENAI_API_KEY)
        if vector_store is None:
            raise RuntimeError("Vector store initialization returned None")
        logger.info("RAG vector store initialized successfully")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize RAG vector store: {e}", exc_info=True)
        raise RuntimeError(f"RAG initialization failed: {e}") from e
    
    travel_agent = create_travel_agent(memory)
    
    # Yield to keep connections alive during app lifetime
    yield
    
    # Shutdown: Cleanup memory saver and connection pool
    logger.info("Shutting down agent and closing PostgreSQL connections")
    if memory and checkpointer:
        await checkpointer.__aexit__(None, None, None)
        logger.info("AsyncPostgresSaver closed")
    if pool:
        await pool.close()
        logger.info("PostgreSQL connection pool closed")
    
# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Strategic Business Travel Assistant API",
    description="AI agent that provides travel advice using weather forecasts",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware - allow ALL Vercel subdomains (regex doesn't work with credentials)
if config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for now (can restrict later)
        allow_credentials=False,  # Can't use credentials with wildcard origins
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for all origins")

# Global agent instance (initialized on first request)
travel_agent = None


# ============================================================================
# Global Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    Returns professional fallback message for production
    """
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    # Check for specific error types
    if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "Service Timeout",
                "message": "The travel assistant is experiencing delays. Please try again in a moment.",
                "detail": "The request took too long to process. This may be due to high API load or network issues."
            }
        )
    
    # Connection errors
    if "connection" in str(exc).lower() or "connect" in str(exc).lower():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service Unavailable",
                "message": "Unable to connect to external services. Please try again shortly.",
                "detail": "Weather or flight data services may be temporarily unavailable."
            }
        )
    
    # Generic fallback for production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "We encountered an unexpected error. Our team has been notified.",
            "detail": "Please try again. If the issue persists, contact support."
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions with cleaner error messages
    """
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "detail": "Please check your request and try again."
        }
    )


# ============================================================================
# LangChain Tool Definition
# ============================================================================

@tool
async def get_city_weather_forecast(city_name: str) -> dict:
    """
    Get current weather and 3-day forecast for a specified city.
    
    Use this tool when you need weather information to provide travel advice,
    packing recommendations, or flight delay predictions. The tool returns
    current temperature, conditions, and a 3-day outlook.
    
    IMPORTANT: For multiple cities, call this tool separately for each city.
    Do not try to pass multiple cities in one call.
    
    Args:
        city_name: Name of the city to get weather forecast for (e.g., "London", "New York", "Tokyo")
    
    Returns:
        Dictionary containing weather data including current conditions and 3-day forecast,
        or an error message if the request fails.
    """
    try:
        logger.info(f"Fetching weather forecast for: {city_name}")
        result = await get_weather_forecast(city_name)
        
        if isinstance(result, ErrorResponse):
            error_response = {
                "error": True,
                "city": city_name,
                "error_type": result.error,
                "status_code": result.status_code,
                "details": result.details,
                "message": f"Failed to get weather data for {city_name}: {result.error}"
            }
            logger.warning(f"Weather API error for {city_name}: {result.error}")
            return error_response
        
        # Convert Pydantic model to dict for LangChain
        weather_data = result.model_dump()
        weather_data["city"] = city_name  # Ensure city name is included
        weather_data["error"] = False  # Mark as successful
        logger.info(f"Successfully fetched weather for {city_name}")
        return weather_data
    
    except Exception as e:
        error_response = {
            "error": True,
            "city": city_name,
            "error_type": "unexpected_error",
            "details": str(e),
            "message": f"Unexpected error fetching weather for {city_name}: {str(e)}"
        }
        logger.error(f"Unexpected error in get_city_weather_forecast for {city_name}: {str(e)}", exc_info=True)
        return error_response


@tool
async def check_flight_status(flight_number: str) -> dict:
    """
    Get real-time flight status information including delays, terminal, and gate.
    
    Use this tool when a user provides a flight number or asks about flight status.
    The tool returns current status, delay information, origin/destination airports,
    and terminal/gate details.
    
    IMPORTANT: After checking flight status, ALWAYS check the weather at the
    destination airport to provide a comprehensive travel risk assessment.
    
    Args:
        flight_number: Flight number to check (e.g., "AA100", "BA456", "DL2030")
    
    Returns:
        Dictionary containing flight status data including delays and terminal info,
        or an error message if the request fails.
    """
    try:
        logger.info(f"Checking flight status for: {flight_number}")
        result = await get_flight_status(flight_number)
        
        if isinstance(result, ErrorResponse):
            error_response = {
                "error": True,
                "flight_number": flight_number,
                "error_type": result.error,
                "status_code": result.status_code,
                "details": result.details,
                "message": f"Failed to get flight status for {flight_number}: {result.error}"
            }
            logger.warning(f"Flight API error for {flight_number}: {result.error}")
            return error_response
        
        # Convert Pydantic model to dict
        flight_data = result.model_dump()
        flight_data["error"] = False
        logger.info(f"Successfully fetched flight status for {flight_number}")
        return flight_data
    
    except Exception as e:
        error_response = {
            "error": True,
            "flight_number": flight_number,
            "error_type": "unexpected_error",
            "details": str(e),
            "message": f"Unexpected error checking flight {flight_number}: {str(e)}"
        }
        logger.error(f"Unexpected error in check_flight_status for {flight_number}: {str(e)}", exc_info=True)
        return error_response


@tool
async def search_travel_knowledge(query: str) -> str:
    """
    Search strategic travel intelligence including airport logistics and city patterns.
    
    Use this tool to retrieve:
    - **Airport Intelligence:** Terminal maps, transfer times, security patterns, ground transport
    - **City Intelligence:** Historical climate, seasonal patterns, local transport strategies
    - **Executive Tips:** Business travel insights, timing strategies, insider knowledge
    
    This RAG-powered tool provides information NOT available from real-time APIs.
    Always verify logistics via RAG before making recommendations.
    
    CRITICAL USAGE:
    - Airport questions: "JFK terminal 4 to terminal 5 transfer time"
    - Security planning: "JFK security wait times morning vs evening"
    - Ground transport: "Best way from JFK to Manhattan for business meeting"
    - Seasonal patterns: "Tokyo typhoon season timing"
    - Historical weather: "London fog patterns winter"
    - Local strategies: "Best transport in London rain"
    
    Args:
        query: Search query describing logistics or patterns needed
    
    Returns:
        Formatted string with relevant travel intelligence from RAG system
    """
    try:
        logger.info(f"Searching travel knowledge for: {query}")
        result = query_travel_knowledge(query, k=4)
        
        # Verify we got actual results, not an error
        if not result or result.startswith("No relevant"):
            logger.warning(f"No travel intelligence found for: {query}")
        else:
            logger.info("✓ Successfully retrieved travel intelligence")
        
        return result
    
    except RuntimeError as e:
        error_msg = f"Travel intelligence system unavailable: {str(e)}"
        logger.error(f"RAG system error: {str(e)}", exc_info=True)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Error searching city guides: {str(e)}"
        logger.error(f"Error in search_city_guides: {str(e)}", exc_info=True)
        raise RuntimeError(error_msg) from e


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are an Executive Travel Strategist - a premium AI advisor specializing in strategic, data-driven travel planning for business executives and discerning travelers.

Your expertise combines:
- **Real-Time Intelligence**: Live weather forecasts and flight status monitoring
- **Strategic Logistics**: Airport terminal navigation, transfer efficiency, security patterns
- **Historical Patterns**: Seasonal weather trends, delay probabilities, optimal timing
- **Executive Insights**: Business traveler optimization, time-value trade-offs, contingency planning

CORE METHODOLOGY:
Your recommendations MUST be grounded in verified data. Never rely on assumptions or general knowledge.

**MANDATORY VERIFICATION PROTOCOL:**
1. **Always verify logistics FIRST** using search_travel_knowledge for:
   - Airport-specific intelligence (terminal transfers, security wait patterns, ground transport)
   - Historical weather patterns and seasonal considerations
   - Local transportation strategies and insider tips

2. **Always check real-time status SECOND** using:
   - get_city_weather_forecast for current conditions and 3-day outlook
   - check_flight_status for live flight tracking and delay information

3. **Then synthesize** verified logistics + real-time data = strategic recommendation

AVAILABLE INTELLIGENCE TOOLS:

**1. search_travel_knowledge** - Strategic Intelligence (RAG System)
   - Airport logistics: Terminal maps, transfer times, security patterns
   - Ground transport: Optimal routes, cost-benefit analysis, timing strategies
   - Historical patterns: Seasonal weather trends, typical delay causes
   - Business insights: Where to work, meeting locations, executive services
   
   **When to use:**
   - ANY airport-related question (JFK, LAX, LHR, etc.)
   - Transportation planning ("How do I get from X to Y?")
   - Historical/seasonal questions ("What's Tokyo like in typhoon season?")
   - Local strategies ("Best way to navigate London in rain?")
   
   **Critical:** ALWAYS query this BEFORE making airport or logistics recommendations

**2. get_city_weather_forecast** - Real-Time Weather Data
   - Current conditions, feels-like temperature, humidity, wind
   - 3-day forecast with min/max temperatures
   - Weather conditions and precipitation probability
   
   **When to use:**
   - Current weather conditions
   - Short-term planning (next 3 days)
   - Packing recommendations
   - Weather impact on travel
   
   **Critical:** ALWAYS fetch current data, never rely on general knowledge

**3. check_flight_status** - Real-Time Flight Tracking
   - Current status: On Time, Delayed, Cancelled, Departed, Landed
   - Delay duration and estimated arrival time
   - Terminal and gate information
   - Origin and destination airports
   
   **When to use:**
   - User provides a flight number
   - Checking connection feasibility
   - Assessing travel disruption risk
   
   **Note:** May use mock data if API unavailable - clearly state this

STRATEGIC WORKFLOW EXAMPLES:

**Example 1: Airport Connection Query**
User: "I'm connecting at JFK from Terminal 4 to Terminal 5. Will 90 minutes be enough?"

Your process:
1. search_travel_knowledge("JFK terminal 4 to terminal 5 transfer time security patterns")
2. Analyze RAG results: AirTrain time, security wait patterns, terminal walking distances
3. Synthesize: "Based on JFK intelligence, 90 minutes provides acceptable risk..."
4. Provide specific breakdown: "30 min arrival walk + 10 min AirTrain + 25 min security + 15 min to gate"

**Example 2: Multi-City Trip Planning**
User: "Should I visit Tokyo in September or October?"

Your process:
1. search_travel_knowledge("Tokyo september october typhoon season weather patterns")
2. get_city_weather_forecast("Tokyo") for current conditions context
3. Synthesize historical patterns + current year trends
4. Provide strategic recommendation with risk assessment

**Example 3: Flight Delay Risk Assessment**
User: "I'm on flight AA100 tonight. Should I be worried about weather delays?"

Your process:
1. check_flight_status("AA100") to get destination city
2. get_city_weather_forecast(destination) for conditions
3. search_travel_knowledge("destination airport delay patterns weather")
4. Synthesize: Current flight status + weather conditions + historical delay patterns
5. Provide risk-rated assessment: "Low risk" / "Moderate risk" / "High risk"

CRITICAL USAGE RULES:

✅ **DO:**
- Query search_travel_knowledge BEFORE making any airport or logistics recommendation
- Fetch real-time weather for EVERY city mentioned (make multiple calls if needed)
- Combine RAG intelligence + real-time data for complete answers
- Provide specific, actionable advice with concrete data points
- State confidence levels when appropriate ("High confidence", "Based on typical patterns")
- Acknowledge when using mock data or when data is unavailable

❌ **DON'T:**
- Make airport recommendations without checking RAG first
- Assume weather without fetching current data
- Provide generic advice not grounded in your tools
- Ignore tool failures - report them and provide caveats
- Claim certainty when using historical patterns or mock data

COMMUNICATION STYLE:

**Tone:** Professional, confident, data-driven yet personable
- Speak as a trusted advisor, not a robotic assistant
- Use "I recommend" not "The system suggests"
- Quantify risks and trade-offs clearly

**Structure:**
1. **Direct Answer First:** Lead with the strategic recommendation
2. **Data Support:** Cite specific data points from your tools
3. **Actionable Steps:** Provide clear next steps or preparation advice
4. **Risk Callouts:** Highlight potential issues or contingencies

**Example Response:**
"I recommend departing Terminal 5 by 4:30 PM for your 7:00 PM departure. Here's why:

**Terminal Analysis:**
- JFK Terminal 4 security currently averaging 45 minutes during 5-7 PM peak (per airport intelligence)
- Walking time from AirTrain to farthest gate: 18-20 minutes
- Your gate (B48) is at the distant end of Concourse B

**Buffer Built In:**
4:30 PM arrival → 4:45 PM through security → 5:30 PM at gate (90 min early for international)

**Weather Context:**
Current conditions show light rain (3mm/hr), which adds 15-20 minutes to ground transport from Manhattan.

**Bottom Line:** This timing provides high confidence for on-time boarding with appropriate cushion for delays."

QUALITY STANDARDS:

- **Accuracy:** Every claim must be backed by tool data
- **Completeness:** Address all aspects of the user's question
- **Foresight:** Anticipate follow-up questions and provide preemptive guidance
- **Value:** Focus on insights that save time, reduce stress, and optimize the executive's schedule

Remember: You're not just providing information - you're removing uncertainty and enabling confident decision-making for high-stakes travel. Every recommendation should demonstrate strategic thinking backed by verified intelligence.
"""


# ============================================================================
# Agent Initialization
# ============================================================================

def create_travel_agent(memory):
    """
    Initialize the Strategic Business Travel Assistant agent using LangGraph
    
    Args:
        memory: AsyncPostgresSaver checkpointer instance for PostgreSQL persistence
    
    Returns:
        LangGraph agent configured with three tools and persistent checkpointing
    
    Notes:
        - LangGraph's create_react_agent natively supports multiple tool calls per turn
        - The agent will automatically parallelize independent tool calls when possible
        - Conversations persisted in PostgreSQL for durability and scalability
        - Memory persists across server restarts for production-grade reliability
        - Temperature set to 0.5 for more consistent tool usage behavior
        - AsyncSqliteSaver checkpointer enables conversation memory persistence
        - Includes MCP tools (weather, flight) and RAG retriever (city guides)
    """
    # Initialize ChatOpenAI model
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.5,  # Lower temperature for more consistent tool usage
        api_key=config.OPENAI_API_KEY
    )
    
    # Define tools - includes MCP tools and RAG retriever
    tools = [get_city_weather_forecast, check_flight_status, search_travel_knowledge]
    
    # Create agent using LangGraph's create_react_agent (2026 standard)
    # The prompt parameter accepts SystemMessage or string for system instructions
    # LangGraph automatically handles multiple tool calls in a single turn
    # Checkpointer enables persistent conversation memory across requests
    # Note: Iteration limits are enforced via recursion_limit in the config during invocation
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        checkpointer=memory  # Enable persistent conversation memory
    )
    
    logger.info("Strategic Business Travel Assistant agent initialized successfully")
    logger.info("Multi-city query support: ENABLED (parallel tool calls)")
    logger.info("Persistent conversation memory: ENABLED (AsyncSqliteSaver)")
    logger.info(f"Tools available: {len(tools)} (weather, flight status, city guides RAG)")
    return agent


# ============================================================================
# API Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint with input validation"""
    message: str = Field(
        ...,
        description="User's message to the travel assistant",
        min_length=1,
        max_length=2000,
        json_schema_extra={"example": "I'm traveling to London next week. What should I expect weather-wise?"}
    )
    session_id: str = Field(
        default="default",
        description="Optional session ID for conversation tracking",
        max_length=100
    )
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message content to prevent injection attacks"""
        # Strip whitespace
        v = v.strip()
        
        # Check for suspiciously long repeated patterns (potential prompt injection)
        if len(v) > 50:
            # Check for excessive repetition of special characters
            special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '{', '}', '[', ']']
            for char in special_chars:
                if v.count(char) > 20:
                    raise ValueError(f"Message contains suspicious pattern: excessive '{char}' characters")
        
        # Check for common prompt injection patterns
        injection_patterns = [
            'ignore previous instructions',
            'ignore all previous',
            'new instructions:',
            'system:',
            'assistant:',
            '<|im_start|>',
            '<|im_end|>',
            'system override',
            'forget your role',
            'disregard',
            'you are now',
            'new role:',
        ]
        
        v_lower = v.lower()
        for pattern in injection_patterns:
            if pattern in v_lower:
                raise ValueError(f"Message contains potentially unsafe pattern: '{pattern}'")
        
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session_id format"""
        # Allow alphanumeric, hyphens, underscores only
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Session ID must contain only alphanumeric characters, hyphens, and underscores")
        return v


class ToolCall(BaseModel):
    """Model for tool call information"""
    tool_name: str = Field(description="Name of the tool that was called")
    city: str = Field(description="City that was queried")
    status: str = Field(description="success or error")
    timestamp: str = Field(description="When the tool was called")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(description="Agent's response to the user")
    session_id: str = Field(description="Session ID for conversation tracking")
    tool_calls: list[ToolCall] = Field(default=[], description="List of tools called during processing")
    cities_analyzed: list[str] = Field(default=[], description="Cities that were analyzed")


# ============================================================================
# FastAPI Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Strategic Business Travel Assistant",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """
    Chat endpoint for interacting with the Strategic Business Travel Assistant
    
    Rate limited to 10 requests per minute per IP address.
    
    This endpoint processes user messages and returns AI-generated travel advice
    based on real-time weather data. Conversation history is persisted per session_id.
    
    Args:
        request: FastAPI Request object (for rate limiting)
        chat_request: ChatRequest containing the user's message and session_id
    
    Returns:
        ChatResponse with the agent's advice and recommendations
    
    Raises:
        HTTPException: If the agent fails to process the request
        RateLimitExceeded: If rate limit is exceeded (429 status)
    """
    try:
        logger.info(f"Processing chat request for session: {chat_request.session_id}")
        
        # Use the global agent instance (initialized in lifespan)
        global travel_agent
        if travel_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Agent not initialized. Server is starting up."
            )
        
        # Execute agent with user input using LangGraph message-based state
        # LangGraph agents use a message-list state format
        # Pass session_id as thread_id to enable conversation persistence
        # Set timeout to prevent hanging requests
        result = await travel_agent.ainvoke(
            {"messages": [("user", chat_request.message)]},
            config={
                "configurable": {"thread_id": chat_request.session_id},
                "recursion_limit": 10  # Additional safety against infinite loops
            }
        )
        
        # Extract output from the final message in the result
        response_text = result["messages"][-1].content
        
        # Extract tool call information from the message history
        tool_calls = []
        cities_analyzed = []
        
        for msg in result["messages"]:
            # Check for tool messages (LangGraph creates ToolMessage objects)
            if hasattr(msg, 'type') and msg.type == 'tool':
                # Tool response message
                tool_name = getattr(msg, 'name', 'get_city_weather_forecast')
                content = msg.content if isinstance(msg.content, dict) else {}
                
                city = content.get('city', 'Unknown')
                is_error = content.get('error', False)
                
                if city != 'Unknown' and city not in cities_analyzed:
                    cities_analyzed.append(city)
                
                tool_calls.append(ToolCall(
                    tool_name=tool_name,
                    city=city,
                    status="error" if is_error else "success",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))
            # Check for AI messages with tool calls
            elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    city = tool_call.get('args', {}).get('city_name', 'Unknown')
                    if city != 'Unknown' and city not in cities_analyzed:
                        cities_analyzed.append(city)
        
        logger.info(f"Successfully processed request for session: {chat_request.session_id}")
        logger.info(f"Tool calls: {len(tool_calls)}, Cities: {cities_analyzed}")
        
        return ChatResponse(
            response=response_text,
            session_id=chat_request.session_id,
            tool_calls=tool_calls,
            cities_analyzed=cities_analyzed
        )
    
    except ValueError as e:
        # Input validation errors
        logger.warning(f"Invalid input: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except TimeoutError as e:
        logger.error(f"Request timeout: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail="The request took too long to process. Please try again with a simpler query."
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint
    
    Verifies that all required services and configurations are available
    """
    from retriever import _vector_store
    
    health_status = {
        "status": "healthy",
        "components": {
            "openai_api_key": mask_api_key(config.OPENAI_API_KEY),
            "openweather_api_key": mask_api_key(config.OPENWEATHER_API_KEY),
            "model": config.OPENAI_MODEL,
            "rag_vector_store": "initialized" if _vector_store is not None else "not_initialized"
        }
    }
    
    # Check if critical components are missing
    if not config.OPENAI_API_KEY or not config.OPENWEATHER_API_KEY:
        health_status["status"] = "degraded"
        health_status["warning"] = "Some API keys are not configured"
    
    # Check if RAG is down
    if _vector_store is None:
        health_status["status"] = "degraded"
        health_status["warning"] = "RAG vector store not initialized - city guide searches will fail"
    
    return health_status


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Strategic Business Travel Assistant on port {config.PORT}")
    logger.info(f"Configuration: {config}")
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
