# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather forecast data using the OpenWeatherMap API.

## Features

- ✅ **get_weather_forecast** tool - Fetch current weather and 3-day forecast for any city
- ✅ Graceful error handling (401 Unauthorized, 404 City Not Found)
- ✅ Pydantic models for type-safe responses
- ✅ Clean JSON output with temperature, conditions, and 3-day outlook
- ✅ Built with FastAPI and FastMCP

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your OpenWeatherMap API key:
   - Get a free API key at [OpenWeatherMap](https://openweathermap.org/api)
   - Copy `.env.example` to `.env`
   - Add your API key to the `.env` file

```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Running the Server

Run the MCP server:
```bash
python server.py
```

Or with environment variables inline:
```bash
OPENWEATHER_API_KEY=your_key_here python server.py
```

### Using the get_weather_forecast Tool

The `get_weather_forecast` tool accepts a `city_name` parameter and returns:

**Response Structure:**
```json
{
  "city": "London",
  "country": "GB",
  "current_temp": 15.2,
  "current_conditions": "partly cloudy",
  "feels_like": 14.1,
  "humidity": 72,
  "wind_speed": 3.5,
  "three_day_outlook": [
    {
      "date": "2026-03-16",
      "temp_min": 12.3,
      "temp_max": 18.5,
      "conditions": "light rain",
      "humidity": 75
    },
    {
      "date": "2026-03-17",
      "temp_min": 13.1,
      "temp_max": 19.2,
      "conditions": "clear sky",
      "humidity": 68
    },
    {
      "date": "2026-03-18",
      "temp_min": 14.5,
      "temp_max": 20.1,
      "conditions": "few clouds",
      "humidity": 65
    }
  ]
}
```

### Error Handling

The server gracefully handles common errors:

**401 Unauthorized (Invalid API Key):**
```json
{
  "error": "Invalid API key. Please check your OPENWEATHER_API_KEY configuration.",
  "status_code": 401,
  "details": "Failed to retrieve weather data for 'London'"
}
```

**404 Not Found (City Not Found):**
```json
{
  "error": "City 'XYZ123' not found. Please check the spelling and try again.",
  "status_code": 404,
  "details": "Failed to retrieve weather data for 'XYZ123'"
}
```

## API Reference

### get_weather_forecast

Fetch current weather and 3-day forecast for a specified city.

**Parameters:**
- `city_name` (str): Name of the city (e.g., "London", "New York", "Tokyo")

**Returns:**
- `WeatherForecastResponse`: Structured weather data with current conditions and 3-day outlook
- `ErrorResponse`: Error details if the request fails

**Example Usage:**
```python
# Call the tool with a city name
result = await get_weather_forecast("London")
```

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
mcp-server/
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── .env.example       # Example environment configuration
└── README.md          # This file
```

## License

MIT License

## Support

For issues or questions:
- OpenWeatherMap API Documentation: https://openweathermap.org/api
- MCP Documentation: https://modelcontextprotocol.io/
