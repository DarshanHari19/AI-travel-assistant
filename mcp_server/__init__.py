"""
MCP Server - Model Context Protocol Tools for Travel Intelligence
Provides weather forecasts and flight status with Redis caching
"""

from .server import (
    get_weather_forecast,
    get_flight_status,
    WeatherForecastResponse,
    FlightStatusResponse,
    ErrorResponse,
    DayForecast,
)

__all__ = [
    "get_weather_forecast",
    "get_flight_status",
    "WeatherForecastResponse",
    "FlightStatusResponse",
    "ErrorResponse",
    "DayForecast",
]

__version__ = "1.0.0"
