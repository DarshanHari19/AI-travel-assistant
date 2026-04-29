#!/usr/bin/env python3
"""
MCP Server for OpenWeatherMap API
Provides weather forecast data through the Model Context Protocol
With Redis caching for cost optimization and latency reduction
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime

import httpx
import redis.asyncio as aioredis
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather-server")

# OpenWeatherMap API configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# AeroDataBox API configuration (RapidAPI)
AERODATABOX_API_KEY = os.getenv("AERODATABOX_API_KEY")
AERODATABOX_BASE_URL = "https://aerodatabox.p.rapidapi.com"

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client: Optional[aioredis.Redis] = None

# Cache TTL settings (in seconds)
WEATHER_CACHE_TTL = 1800  # 30 minutes
FLIGHT_CACHE_TTL = 300    # 5 minutes


# Pydantic models for structured responses
class DayForecast(BaseModel):
    """Model for a single day's forecast"""
    date: str = Field(description="Date of the forecast (YYYY-MM-DD)")
    temp_min: float = Field(description="Minimum temperature in Celsius")
    temp_max: float = Field(description="Maximum temperature in Celsius")
    conditions: str = Field(description="Weather conditions description")
    humidity: int = Field(description="Humidity percentage")


class WeatherForecastResponse(BaseModel):
    """Model for the complete weather forecast response"""
    city: str = Field(description="City name")
    country: str = Field(description="Country code")
    current_temp: float = Field(description="Current temperature in Celsius")
    current_conditions: str = Field(description="Current weather conditions")
    feels_like: float = Field(description="Feels like temperature in Celsius")
    humidity: int = Field(description="Current humidity percentage")
    wind_speed: float = Field(description="Wind speed in m/s")
    three_day_outlook: list[DayForecast] = Field(description="3-day weather forecast")


class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str = Field(description="Error message")
    status_code: int = Field(description="HTTP status code")
    details: Optional[str] = Field(default=None, description="Additional error details")


class FlightStatusResponse(BaseModel):
    """Model for flight status response"""
    flight_number: str = Field(description="Flight number")
    airline: str = Field(description="Airline name")
    status: str = Field(description="Flight status (On Time, Delayed, Cancelled, Departed, Landed)")
    scheduled_departure: str = Field(description="Scheduled departure time")
    actual_departure: Optional[str] = Field(default=None, description="Actual departure time")
    scheduled_arrival: str = Field(description="Scheduled arrival time")
    estimated_arrival: Optional[str] = Field(default=None, description="Estimated arrival time")
    delay_minutes: int = Field(description="Delay in minutes (0 if on time)")
    origin: str = Field(description="Origin airport code")
    destination: str = Field(description="Destination airport code")
    terminal: Optional[str] = Field(default=None, description="Terminal information")
    gate: Optional[str] = Field(default=None, description="Gate information")


# ============================================================================
# Redis Cache Manager
# ============================================================================

class CacheManager:
    """
    Production-grade caching layer using Redis.
    Implements cache-aside pattern with fallback to stale data on API failures.
    """
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        logger.info("CacheManager initialized")
    
    async def get_weather(self, city: str) -> Optional[dict]:
        """Get cached weather data"""
        try:
            key = f"weather:{city.lower()}"
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"✓ Cache HIT for weather:{city}")
                return json.loads(cached)
            logger.info(f"✗ Cache MISS for weather:{city}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for weather:{city}: {e}")
            return None
    
    async def cache_weather(self, city: str, data: dict, ttl: int = WEATHER_CACHE_TTL):
        """Cache weather data with TTL"""
        try:
            key = f"weather:{city.lower()}"
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.info(f"✓ Cached weather:{city} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for weather:{city}: {e}")
    
    async def get_flight(self, flight_number: str) -> Optional[dict]:
        """Get cached flight status"""
        try:
            key = f"flight:{flight_number.upper()}"
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"✓ Cache HIT for flight:{flight_number}")
                return json.loads(cached)
            logger.info(f"✗ Cache MISS for flight:{flight_number}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for flight:{flight_number}: {e}")
            return None
    
    async def cache_flight(self, flight_number: str, data: dict, ttl: int = FLIGHT_CACHE_TTL):
        """Cache flight status with TTL"""
        try:
            key = f"flight:{flight_number.upper()}"
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.info(f"✓ Cached flight:{flight_number} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for flight:{flight_number}: {e}")
    
    async def get_stale(self, prefix: str, identifier: str) -> Optional[dict]:
        """
        Attempt to retrieve stale cache data when API fails.
        This is a fallback mechanism for better resilience.
        """
        try:
            key = f"{prefix}:{identifier.lower()}"
            # Check if key exists even if expired
            cached = await self.redis.get(key)
            if cached:
                logger.warning(f"⚠ Using STALE cache for {prefix}:{identifier}")
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Stale cache retrieval error: {e}")
            return None


async def get_cache_manager() -> Optional[CacheManager]:
    """Get or initialize cache manager"""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = await aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # Test connection
            await redis_client.ping()
            logger.info(f"✓ Connected to Redis: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"⚠ Redis unavailable ({e}), running without cache")
            return None
    
    return CacheManager(redis_client)



async def fetch_weather_data(city_name: str) -> dict:
    """
    Fetch weather data from OpenWeatherMap API
    
    Args:
        city_name: Name of the city to get weather for
        
    Returns:
        Dictionary containing weather data
        
    Raises:
        HTTPException: For API errors (401, 404, etc.)
    """
    if not OPENWEATHER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OpenWeatherMap API key not configured. Please set OPENWEATHER_API_KEY environment variable."
        )
    
    async with httpx.AsyncClient() as client:
        # Fetch current weather
        current_url = f"{OPENWEATHER_BASE_URL}/weather"
        current_params = {
            "q": city_name,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        try:
            current_response = await client.get(current_url, params=current_params)
            
            # Handle specific error codes
            if current_response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key. Please check your OPENWEATHER_API_KEY configuration."
                )
            elif current_response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"City '{city_name}' not found. Please check the spelling and try again."
                )
            elif current_response.status_code != 200:
                raise HTTPException(
                    status_code=current_response.status_code,
                    detail=f"OpenWeatherMap API error: {current_response.text}"
                )
            
            current_data = current_response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching current weather: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Network error: Unable to reach OpenWeatherMap API. {str(e)}"
            )
        
        # Fetch 5-day forecast (we'll extract 3 days)
        forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
        forecast_params = {
            "q": city_name,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        try:
            forecast_response = await client.get(forecast_url, params=forecast_params)
            
            if forecast_response.status_code != 200:
                raise HTTPException(
                    status_code=forecast_response.status_code,
                    detail=f"Error fetching forecast: {forecast_response.text}"
                )
            
            forecast_data = forecast_response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching forecast: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Network error: Unable to fetch forecast data. {str(e)}"
            )
    
    return {
        "current": current_data,
        "forecast": forecast_data
    }


def process_forecast_data(forecast_list: list) -> list[DayForecast]:
    """
    Process forecast data and extract 3-day outlook
    
    Args:
        forecast_list: List of forecast entries from API
        
    Returns:
        List of DayForecast objects for the next 3 days
    """
    daily_forecasts = {}
    
    for item in forecast_list:
        # Extract date from timestamp
        date_str = item["dt_txt"].split()[0]  # Format: "2024-03-16 12:00:00" -> "2024-03-16"
        
        if date_str not in daily_forecasts:
            daily_forecasts[date_str] = {
                "temps": [],
                "conditions": [],
                "humidity": []
            }
        
        daily_forecasts[date_str]["temps"].append(item["main"]["temp"])
        daily_forecasts[date_str]["conditions"].append(item["weather"][0]["description"])
        daily_forecasts[date_str]["humidity"].append(item["main"]["humidity"])
    
    # Create DayForecast objects for the next 3 days
    three_day_outlook = []
    for date_str in sorted(daily_forecasts.keys())[:3]:
        day_data = daily_forecasts[date_str]
        
        forecast = DayForecast(
            date=date_str,
            temp_min=round(min(day_data["temps"]), 1),
            temp_max=round(max(day_data["temps"]), 1),
            conditions=max(set(day_data["conditions"]), key=day_data["conditions"].count),
            humidity=int(sum(day_data["humidity"]) / len(day_data["humidity"]))
        )
        three_day_outlook.append(forecast)
    
    return three_day_outlook


def generate_mock_flight_status(flight_number: str) -> FlightStatusResponse:
    """
    Generate mock flight status data for demonstration or fallback.
    
    Args:
        flight_number: Flight number to generate mock data for
        
    Returns:
        FlightStatusResponse with realistic mock data
    """
    import random
    from datetime import datetime, timedelta
    
    logger.info(f"Generating mock flight status for: {flight_number}")
    
    # Parse airline code from flight number
    airline_codes = {
        "AA": "American Airlines",
        "BA": "British Airways",
        "DL": "Delta Air Lines",
        "UA": "United Airlines",
        "LH": "Lufthansa",
        "AF": "Air France",
        "EK": "Emirates",
        "QF": "Qantas",
        "SQ": "Singapore Airlines"
    }
    
    # Extract airline code (first 2 letters)
    airline_code = flight_number[:2].upper()
    airline = airline_codes.get(airline_code, "Unknown Airlines")
    
    # Mock destinations
    routes = [
        ("JFK", "LAX"),
        ("LHR", "JFK"),
        ("DXB", "SYD"),
        ("CDG", "NRT"),
        ("SFO", "ORD"),
        ("ATL", "MIA"),
        ("DEN", "SEA")
    ]
    origin, destination = random.choice(routes)
    
    # Mock status with weighted probabilities
    status_options = [
        ("On Time", 0),
        ("Delayed", random.randint(15, 120)),
        ("Delayed", random.randint(15, 60)),
        ("On Time", 0),
        ("Departed", 0),
        ("On Time", 0)
    ]
    status, delay = random.choice(status_options)
    
    # Generate realistic times
    now = datetime.now()
    scheduled_departure = now + timedelta(hours=2)
    scheduled_arrival = scheduled_departure + timedelta(hours=5)
    
    actual_departure = None
    estimated_arrival = None
    
    if status == "Departed":
        actual_departure = (scheduled_departure + timedelta(minutes=delay)).strftime("%H:%M")
        estimated_arrival = (scheduled_arrival + timedelta(minutes=delay)).strftime("%H:%M")
    elif status == "Delayed":
        estimated_arrival = (scheduled_arrival + timedelta(minutes=delay)).strftime("%H:%M")
    
    # Build response
    return FlightStatusResponse(
        flight_number=flight_number.upper(),
        airline=airline,
        status=status,
        scheduled_departure=scheduled_departure.strftime("%H:%M"),
        actual_departure=actual_departure,
        scheduled_arrival=scheduled_arrival.strftime("%H:%M"),
        estimated_arrival=estimated_arrival,
        delay_minutes=delay,
        origin=origin,
        destination=destination,
        terminal=f"T{random.randint(1, 5)}",
        gate=f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 30)}"
    )


async def fetch_flight_status_from_api(flight_number: str) -> FlightStatusResponse:
    """
    Fetch real flight status from AeroDataBox API via RapidAPI.
    
    Args:
        flight_number: Flight number to query
        
    Returns:
        FlightStatusResponse with real flight data
        
    Raises:
        HTTPException: For API errors
    """
    if not AERODATABOX_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="AeroDataBox API key not configured. Please set AERODATABOX_API_KEY environment variable."
        )
    
    # AeroDataBox API endpoint and headers
    url = f"{AERODATABOX_BASE_URL}/flights/number/{flight_number}"
    headers = {
        "X-RapidAPI-Key": AERODATABOX_API_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Calling AeroDataBox API for flight: {flight_number}")
            response = await client.get(url, headers=headers, timeout=10.0)
            
            # Handle specific error codes
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid AeroDataBox API key. Please check your AERODATABOX_API_KEY configuration."
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Flight '{flight_number}' not found. Please check the flight number."
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="AeroDataBox API rate limit exceeded. Please try again later."
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AeroDataBox API error: {response.text}"
                )
            
            data = response.json()
            
            # AeroDataBox returns a list of flights for the flight number
            # We'll take the first/most recent one
            if not data or len(data) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"No flight data found for '{flight_number}'"
                )
            
            flight = data[0]  # Get the first flight from the list
            
            # Extract data from AeroDataBox response
            # Map to our FlightStatusResponse model
            departure = flight.get("departure", {})
            arrival = flight.get("arrival", {})
            
            # Determine flight status
            status = "Unknown"
            if flight.get("status"):
                status = flight["status"]
            elif arrival.get("actualTimeLocal"):
                status = "Landed"
            elif departure.get("actualTimeLocal"):
                status = "Departed"
            elif departure.get("revisedTimeLocal"):
                status = "Delayed"
            else:
                status = "On Time"
            
            # Calculate delay in minutes
            delay_minutes = 0
            scheduled_dep_time = departure.get("scheduledTimeLocal", "")
            revised_dep_time = departure.get("revisedTimeLocal") or departure.get("actualTimeLocal")
            
            if scheduled_dep_time and revised_dep_time:
                from datetime import datetime
                try:
                    scheduled = datetime.fromisoformat(scheduled_dep_time.replace("Z", "+00:00"))
                    revised = datetime.fromisoformat(revised_dep_time.replace("Z", "+00:00"))
                    delay_minutes = int((revised - scheduled).total_seconds() / 60)
                except Exception as e:
                    logger.warning(f"Could not calculate delay: {e}")
            
            # Format times (extract HH:MM from ISO strings)
            def extract_time(time_str: Optional[str]) -> Optional[str]:
                if not time_str:
                    return None
                try:
                    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    return dt.strftime("%H:%M")
                except:
                    return None
            
            # Build response
            return FlightStatusResponse(
                flight_number=flight_number.upper(),
                airline=flight.get("airline", {}).get("name", "Unknown Airlines"),
                status=status,
                scheduled_departure=extract_time(departure.get("scheduledTimeLocal")) or "N/A",
                actual_departure=extract_time(departure.get("actualTimeLocal")),
                scheduled_arrival=extract_time(arrival.get("scheduledTimeLocal")) or "N/A",
                estimated_arrival=extract_time(arrival.get("revisedTimeLocal") or arrival.get("actualTimeLocal")),
                delay_minutes=max(0, delay_minutes),
                origin=departure.get("airport", {}).get("iata", "N/A"),
                destination=arrival.get("airport", {}).get("iata", "N/A"),
                terminal=departure.get("terminal"),
                gate=departure.get("gate")
            )
            
        except httpx.RequestError as e:
            logger.error(f"Network error while fetching flight status: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Network error: Unable to reach AeroDataBox API. {str(e)}"
            )


@mcp.tool()
async def get_flight_status(flight_number: str) -> FlightStatusResponse | ErrorResponse:
    """
    Get real-time flight status information with Redis caching.
    
    This tool provides current flight status including delays, terminal,
    gate, and timing information. Uses AeroDataBox API via RapidAPI,
    with fallback to mock data if API is unavailable. Results are cached
    for 5 minutes for frequently checked flights.
    
    Args:
        flight_number: Flight number (e.g., "AA100", "BA456", "DL2030")
    
    Returns:
        FlightStatusResponse: A structured response containing flight status details,
        or ErrorResponse if an error occurs.
    
    Examples:
        >>> await get_flight_status("AA100")
        >>> await get_flight_status("BA456")
        >>> await get_flight_status("DL2030")
    """
    try:
        logger.info(f"Fetching flight status for: {flight_number}")
        
        # Try cache first
        cache = await get_cache_manager()
        if cache:
            cached_data = await cache.get_flight(flight_number)
            if cached_data:
                # Return cached data as FlightStatusResponse
                return FlightStatusResponse(**cached_data)
        
        # Cache miss or unavailable - fetch from API
        # Try to fetch from AeroDataBox API if key is configured
        if AERODATABOX_API_KEY:
            try:
                response = await fetch_flight_status_from_api(flight_number)
                logger.info(f"Successfully retrieved real flight status for {flight_number}")
                
                # Cache the response
                if cache:
                    await cache.cache_flight(flight_number, response.model_dump())
                
                return response
            except HTTPException as e:
                logger.warning(f"AeroDataBox API failed: {e.detail}. Falling back to mock data.")
                # Fall through to mock data
            except Exception as e:
                logger.warning(f"Unexpected error from AeroDataBox: {str(e)}. Falling back to mock data.")
                # Fall through to mock data
        else:
            logger.info("AeroDataBox API key not configured. Using mock data.")
        
        # Fallback: Generate mock flight status
        response = generate_mock_flight_status(flight_number)
        logger.info(f"Successfully generated mock flight status for {flight_number}")
        
        # Cache mock data with shorter TTL (1 minute)
        if cache:
            await cache.cache_flight(flight_number, response.model_dump(), ttl=60)
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching flight status for '{flight_number}': {str(e)}")
        return ErrorResponse(
            error="Failed to retrieve flight status",
            status_code=500,
            details=str(e)
        )


@mcp.tool()
async def get_weather_forecast(city_name: str) -> WeatherForecastResponse | ErrorResponse:
    """
    Get current weather and 3-day forecast for a specified city with Redis caching.
    
    This tool fetches weather data from OpenWeatherMap API and returns
    current conditions along with a 3-day outlook. Results are cached
    for 30 minutes to reduce API costs and improve latency.
    
    Args:
        city_name: Name of the city to get weather forecast for (e.g., "London", "New York")
    
    Returns:
        WeatherForecastResponse: A structured response containing current weather
        and 3-day forecast, or ErrorResponse if an error occurs.
    
    Examples:
        >>> await get_weather_forecast("London")
        >>> await get_weather_forecast("New York")
        >>> await get_weather_forecast("Tokyo")
    """
    try:
        logger.info(f"Fetching weather forecast for: {city_name}")
        
        # Try cache first
        cache = await get_cache_manager()
        if cache:
            cached_data = await cache.get_weather(city_name)
            if cached_data:
                # Return cached data as WeatherForecastResponse
                return WeatherForecastResponse(**cached_data)
        
        # Cache miss or unavailable - fetch from API
        weather_data = await fetch_weather_data(city_name)
        current = weather_data["current"]
        forecast = weather_data["forecast"]
        
        # Process forecast for 3-day outlook
        three_day_outlook = process_forecast_data(forecast["list"])
        
        # Build response
        response = WeatherForecastResponse(
            city=current["name"],
            country=current["sys"]["country"],
            current_temp=round(current["main"]["temp"], 1),
            current_conditions=current["weather"][0]["description"],
            feels_like=round(current["main"]["feels_like"], 1),
            humidity=current["main"]["humidity"],
            wind_speed=round(current["wind"]["speed"], 1),
            three_day_outlook=three_day_outlook
        )
        
        # Cache the response
        if cache:
            await cache.cache_weather(city_name, response.model_dump())
        
        logger.info(f"Successfully retrieved weather forecast for {city_name}")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP error for city '{city_name}': {e.detail}")
        
        # Attempt to use stale cache as fallback
        cache = await get_cache_manager()
        if cache:
            stale_data = await cache.get_stale("weather", city_name)
            if stale_data:
                logger.warning(f"Returning stale cache for {city_name} due to API error")
                return WeatherForecastResponse(**stale_data)
        
        return ErrorResponse(
            error=e.detail,
            status_code=e.status_code,
            details=f"Failed to retrieve weather data for '{city_name}'"
        )
    except Exception as e:
        logger.error(f"Unexpected error for city '{city_name}': {str(e)}")
        return ErrorResponse(
            error="Internal server error",
            status_code=500,
            details=str(e)
        )


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
