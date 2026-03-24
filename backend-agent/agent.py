#!/usr/bin/env python3
"""
LangChain Backend Agent - Strategic Business Travel Assistant
Integrates with OpenWeatherMap MCP server to provide travel advice
"""

import os
import sys
import logging
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

# Import secure configuration
from config import config, mask_api_key

# Add mcp-server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server'))
from server import get_weather_forecast, WeatherForecastResponse, ErrorResponse

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

# Initialize FastAPI app
app = FastAPI(
    title="Strategic Business Travel Assistant API",
    description="AI agent that provides travel advice using weather forecasts",
    version="1.0.0"
)

# Add CORS middleware with configurable origins
if config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {config.ALLOWED_ORIGINS}")


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


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a Strategic Business Travel Assistant powered by real-time weather intelligence.

Your expertise includes:
- Analyzing weather patterns to predict potential flight delays and disruptions
- Providing tailored packing recommendations based on destination weather
- Advising on optimal travel times considering weather conditions
- Warning about weather-related risks (storms, extreme temperatures, etc.)
- Suggesting contingency plans for weather-affected travel

CRITICAL TOOL USAGE RULES:
1. **ALWAYS use the get_city_weather_forecast tool** - Never rely on general knowledge or typical weather patterns
2. **For MULTIPLE cities**: You MUST call get_city_weather_forecast separately for EACH city mentioned
3. **Before comparisons**: Fetch real-time data for ALL cities first, then compare
4. **If a tool call fails**: Report the specific error for that city, but continue with available data for other cities
5. **No assumptions**: Even for well-known cities, always fetch current data

When a user asks about travel to one or more cities:
1. **MANDATORY**: Use get_city_weather_forecast tool for EVERY city mentioned (make multiple calls if needed)
2. Wait for all tool results before formulating your response
3. Analyze temperature ranges, precipitation, wind conditions, and humidity from the actual data
4. Provide actionable advice on:
   - Potential flight delays (high winds, storms, visibility issues)
   - Essential items to pack (umbrella, layers, sunscreen, etc.)
   - Best times to travel within the forecast period
   - Any weather-related alerts or concerns
5. For multi-city queries, provide side-by-side comparisons using the real data you fetched

Examples of correct behavior:
- User: "Compare London and Paris weather" → Call tool for London, call tool for Paris, then compare
- User: "Which is better: Tokyo or Seoul?" → Call tool for Tokyo, call tool for Seoul, then advise
- User: "Should I visit New York or Miami?" → Call tool for New York, call tool for Miami, then recommend

Communication Style:
- Be professional yet friendly and conversational
- Provide specific, actionable recommendations based on REAL DATA from tools
- Use concrete data points (temperatures, conditions) to support your advice
- If a city's data is unavailable, explicitly state that and work with available information
- Prioritize safety and comfort
- Be concise but thorough

REMEMBER: You have access to real-time weather data via tools. NEVER guess or use general knowledge when tool data is available. For multiple cities, make multiple tool calls - this is REQUIRED behavior.
"""


# ============================================================================
# Agent Initialization
# ============================================================================

def create_travel_agent():
    """
    Initialize the Strategic Business Travel Assistant agent using LangGraph
    
    Returns:
        LangGraph agent configured with the weather forecast tool
    
    Notes:
        - LangGraph's create_react_agent natively supports multiple tool calls per turn
        - The agent will automatically parallelize independent tool calls when possible
        - Temperature set to 0.5 for more consistent tool usage behavior
    """
    # Initialize ChatOpenAI model
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.5,  # Lower temperature for more consistent tool usage
        api_key=config.OPENAI_API_KEY,
        model_kwargs={"top_p": 0.9}
    )
    
    # Define tools
    tools = [get_city_weather_forecast]
    
    # Create agent using LangGraph's create_react_agent (2026 standard)
    # The prompt parameter accepts SystemMessage or string for system instructions
    # LangGraph automatically handles multiple tool calls in a single turn
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=SYSTEM_PROMPT)
    )
    
    logger.info("Strategic Business Travel Assistant agent initialized successfully")
    logger.info("Multi-city query support: ENABLED (parallel tool calls)")
    return agent


# ============================================================================
# API Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(
        ...,
        description="User's message to the travel assistant",
        example="I'm traveling to London next week. What should I expect weather-wise?"
    )
    session_id: str = Field(
        default="default",
        description="Optional session ID for conversation tracking"
    )


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
async def chat(request: ChatRequest):
    """
    Chat endpoint for interacting with the Strategic Business Travel Assistant
    
    This endpoint processes user messages and returns AI-generated travel advice
    based on real-time weather data.
    
    Args:
        request: ChatRequest containing the user's message
    
    Returns:
        ChatResponse with the agent's advice and recommendations
    
    Raises:
        HTTPException: If the agent fails to process the request
    """
    try:
        from datetime import datetime
        
        logger.info(f"Processing chat request for session: {request.session_id}")
        
        # Create LangGraph agent
        agent = create_travel_agent()
        
        # Execute agent with user input using LangGraph message-based state
        # LangGraph agents use a message-list state format
        result = await agent.ainvoke({
            "messages": [("user", request.message)]
        })
        
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
                    timestamp=datetime.utcnow().isoformat()
                ))
            # Check for AI messages with tool calls
            elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    city = tool_call.get('args', {}).get('city_name', 'Unknown')
                    if city != 'Unknown' and city not in cities_analyzed:
                        cities_analyzed.append(city)
        
        logger.info(f"Successfully processed request for session: {request.session_id}")
        logger.info(f"Tool calls: {len(tool_calls)}, Cities: {cities_analyzed}")
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            tool_calls=tool_calls,
            cities_analyzed=cities_analyzed
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
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
    health_status = {
        "status": "healthy",
        "components": {
            "openai_api_key": mask_api_key(config.OPENAI_API_KEY),
            "openweather_api_key": mask_api_key(config.OPENWEATHER_API_KEY),
            "model": config.OPENAI_MODEL
        }
    }
    
    # Check if critical components are missing
    if not config.OPENAI_API_KEY or not config.OPENWEATHER_API_KEY:
        health_status["status"] = "degraded"
        health_status["warning"] = "Some API keys are not configured"
    
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
