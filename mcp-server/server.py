#!/usr/bin/env python3
"""
MCP Server for OpenWeatherMap API
Provides weather forecast data through the Model Context Protocol
"""

import os
import logging
from typing import Optional
from datetime import datetime

import httpx
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather-server")

# OpenWeatherMap API configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


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


@mcp.tool()
async def get_weather_forecast(city_name: str) -> WeatherForecastResponse | ErrorResponse:
    """
    Get current weather and 3-day forecast for a specified city.
    
    This tool fetches weather data from OpenWeatherMap API and returns
    current conditions along with a 3-day outlook including temperature
    ranges, weather conditions, and humidity levels.
    
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
        
        # Fetch weather data
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
        
        logger.info(f"Successfully retrieved weather forecast for {city_name}")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP error for city '{city_name}': {e.detail}")
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
