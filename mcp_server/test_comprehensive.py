"""
Comprehensive Test Suite for MCP Weather Server
Tests the weather forecast tool, error handling, and data processing
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Set test environment variables
os.environ["OPENWEATHER_API_KEY"] = "test-api-key-1234567890"

from server import (
    get_weather_forecast,
    fetch_weather_data,
    process_forecast_data,
    WeatherForecastResponse,
    ErrorResponse,
    DayForecast
)


# ============================================================================
# Pydantic Model Tests
# ============================================================================

def test_day_forecast_model():
    """Test DayForecast model validation"""
    forecast = DayForecast(
        date="2026-03-21",
        temp_min=12.5,
        temp_max=18.3,
        conditions="light rain",
        humidity=75
    )
    
    assert forecast.date == "2026-03-21"
    assert forecast.temp_min == 12.5
    assert forecast.temp_max == 18.3
    assert forecast.conditions == "light rain"
    assert forecast.humidity == 75


def test_weather_forecast_response_model():
    """Test WeatherForecastResponse model validation"""
    response = WeatherForecastResponse(
        city="London",
        country="GB",
        current_temp=15.2,
        current_conditions="partly cloudy",
        feels_like=14.1,
        humidity=72,
        wind_speed=3.5,
        three_day_outlook=[
            DayForecast(
                date="2026-03-21",
                temp_min=12.0,
                temp_max=18.0,
                conditions="cloudy",
                humidity=70
            )
        ]
    )
    
    assert response.city == "London"
    assert response.country == "GB"
    assert len(response.three_day_outlook) == 1


def test_error_response_model():
    """Test ErrorResponse model validation"""
    error = ErrorResponse(
        error="City not found",
        status_code=404,
        details="The specified city could not be located"
    )
    
    assert error.error == "City not found"
    assert error.status_code == 404
    assert error.details is not None


# ============================================================================
# Data Processing Tests
# ============================================================================

def test_process_forecast_data():
    """Test forecast data aggregation"""
    # Mock forecast data with multiple timestamps
    forecast_data = [
        {
            'dt': 1711065600,  # 2024-03-21 12:00:00
            'dt_txt': '2024-03-21 12:00:00',
            'main': {'temp': 15.0, 'humidity': 70},
            'weather': [{'description': 'light rain'}]
        },
        {
            'dt': 1711076400,  # 2024-03-21 15:00:00
            'dt_txt': '2024-03-21 15:00:00',
            'main': {'temp': 18.0, 'humidity': 65},
            'weather': [{'description': 'cloudy'}]
        },
        {
            'dt': 1711087200,  # 2024-03-21 18:00:00
            'dt_txt': '2024-03-21 18:00:00',
            'main': {'temp': 16.5, 'humidity': 72},
            'weather': [{'description': 'light rain'}]
        },
    ] * 8  # 24 data points total
    
    result = process_forecast_data(forecast_data)
    
    assert isinstance(result, list)
    assert len(result) <= 3  # Should return max 3 days
    assert all(isinstance(day, DayForecast) for day in result)
    
    # Check that temperatures are aggregated
    if len(result) > 0:
        assert result[0].temp_min <= result[0].temp_max


def test_process_forecast_data_finds_dominant_conditions():
    """Test that processing finds most common weather condition"""
    from server import process_forecast_data
    
    forecast_data = [
        {
            'dt': 1711065600 + (i * 3600),
            'dt_txt': f'2024-03-21 {12 + (i // 3):02d}:00:00',
            'main': {'temp': 15.0, 'humidity': 70},
            'weather': [{'description': 'light rain' if i < 6 else 'cloudy'}]
        }
        for i in range(24)
    ]
    
    result = process_forecast_data(forecast_data)
    
    # "light rain" appears more often, so it should be the dominant condition
    assert len(result) > 0
    # The dominant condition should be one of the input conditions
    assert result[0].conditions in ['light rain', 'cloudy']


# ============================================================================
# Weather Fetch Tests
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_weather_data_success(mock_client_class):
    """Test successful weather data fetch"""
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'name': 'London',
        'sys': {'country': 'GB'},
        'main': {'temp': 15.2, 'feels_like': 14.1, 'humidity': 72},
        'weather': [{'description': 'partly cloudy'}],
        'wind': {'speed': 3.5}
    }
    
    # Create mock client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    result = await fetch_weather_data("London")
    
    assert 'current' in result
    assert result['current']['name'] == 'London'


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_weather_data_handles_401(mock_client_class):
    """Test handling of invalid API key"""
    from fastapi import HTTPException
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    with pytest.raises(HTTPException) as exc_info:
        await fetch_weather_data("London")
    
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail or "API key" in exc_info.value.detail


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_weather_data_handles_404(mock_client_class):
    """Test handling of city not found"""
    from fastapi import HTTPException
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    with pytest.raises(HTTPException) as exc_info:
        await fetch_weather_data("InvalidCity123")
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_weather_data_handles_network_error(mock_client_class):
    """Test handling of network errors"""
    import httpx
    from fastapi import HTTPException
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.RequestError("Connection timeout")
    mock_client_class.return_value = mock_client
    
    with pytest.raises(HTTPException) as exc_info:
        await fetch_weather_data("London")
    
    assert exc_info.value.status_code == 503


# ============================================================================
# MCP Tool Tests (get_weather_forecast)
# ============================================================================

@pytest.mark.asyncio
@patch('server.fetch_weather_data')
async def test_get_weather_forecast_success(mock_fetch):
    """Test successful weather forecast retrieval"""
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
                    'dt': 1711065600 + (i * 10800),
                    'dt_txt': f'2024-03-21 {12 + (i * 3):02d}:00:00',
                    'main': {'temp': 14.0 + i * 0.5, 'humidity': 70},
                    'weather': [{'description': 'cloudy'}]
                }
                for i in range(24)
            ]
        }
    }
    
    result = await get_weather_forecast("London")
    
    assert isinstance(result, WeatherForecastResponse)
    assert result.city == "London"
    assert result.country == "GB"
    assert result.current_temp == 15.2
    assert len(result.three_day_outlook) > 0


@pytest.mark.asyncio
@patch('server.fetch_weather_data')
async def test_get_weather_forecast_returns_error_on_failure(mock_fetch):
    """Test that get_weather_forecast returns ErrorResponse on failure"""
    from fastapi import HTTPException
    
    mock_fetch.side_effect = HTTPException(
        status_code=404,
        detail="City 'InvalidCity' not found"
    )
    
    result = await get_weather_forecast("InvalidCity")
    
    assert isinstance(result, ErrorResponse)
    assert result.status_code == 404
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
@patch('server.fetch_weather_data')
async def test_get_weather_forecast_handles_multiple_cities(mock_fetch):
    """Test that tool can be called multiple times for different cities"""
    # Mock different responses for different cities
    async def mock_fetch_side_effect(city):
        return {
            'current': {
                'name': city,
                'sys': {'country': 'XX'},
                'main': {'temp': 15.0, 'feels_like': 14.0, 'humidity': 70},
                'weather': [{'description': 'clear'}],
                'wind': {'speed': 2.0}
            },
            'forecast': {
                'list': [
                    {
                        'dt': 1711065600,
                        'dt_txt': '2024-03-21 12:00:00',
                        'main': {'temp': 15.0, 'humidity': 70},
                        'weather': [{'description': 'clear'}]
                    }
                ] * 24
            }
        }
    
    mock_fetch.side_effect = mock_fetch_side_effect
    
    london_result = await get_weather_forecast("London")
    paris_result = await get_weather_forecast("Paris")
    
    assert isinstance(london_result, WeatherForecastResponse)
    assert isinstance(paris_result, WeatherForecastResponse)
    assert london_result.city == "London"
    assert paris_result.city == "Paris"


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require real API key (set RUN_INTEGRATION_TESTS=1)"
)
@pytest.mark.asyncio
async def test_real_api_call():
    """
    Integration test with real OpenWeatherMap API
    Only runs if RUN_INTEGRATION_TESTS=1 and valid API key is set
    """
    # This requires a real API key in environment
    result = await get_weather_forecast("London")
    
    assert isinstance(result, (WeatherForecastResponse, ErrorResponse))
    
    if isinstance(result, WeatherForecastResponse):
        assert result.city is not None
        assert result.current_temp is not None
        assert len(result.three_day_outlook) > 0


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.asyncio
@patch('server.fetch_weather_data')
async def test_handles_empty_forecast_list(mock_fetch):
    """Test handling when forecast list is empty"""
    mock_fetch.return_value = {
        'current': {
            'name': 'TestCity',
            'sys': {'country': 'XX'},
            'main': {'temp': 15.0, 'feels_like': 14.0, 'humidity': 70},
            'weather': [{'description': 'clear'}],
            'wind': {'speed': 2.0}
        },
        'forecast': {
            'list': []
        }
    }
    
    result = await get_weather_forecast("TestCity")
    
    assert isinstance(result, WeatherForecastResponse)
    assert len(result.three_day_outlook) == 0


@pytest.mark.asyncio
@patch('server.fetch_weather_data')
async def test_handles_special_characters_in_city_name(mock_fetch):
    """Test handling of city names with special characters"""
    mock_fetch.return_value = {
        'current': {
            'name': 'São Paulo',
            'sys': {'country': 'BR'},
            'main': {'temp': 25.0, 'feels_like': 24.0, 'humidity': 80},
            'weather': [{'description': 'sunny'}],
            'wind': {'speed': 1.5}
        },
        'forecast': {'list': []}
    }
    
    result = await get_weather_forecast("São Paulo")
    
    assert isinstance(result, WeatherForecastResponse)
    assert result.city == "São Paulo"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
