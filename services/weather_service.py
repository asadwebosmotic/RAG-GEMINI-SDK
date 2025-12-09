import logging
from typing import Dict
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def get_weather(location: str, unit: str = "metric") -> Dict:
    """
    Get weather data using OpenWeatherMap API.
    
    Args:
        location: City name or location
        unit: Temperature unit ("metric" for Celsius, "imperial" for Fahrenheit)
    
    Returns:
        Dictionary with weather data
    """
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": settings.WEATHER_API_KEY,
                "units": unit
            }
            
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "location": location,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "unit": unit
            }
            
            logger.info(f"Weather fetched for: {location}")
            return result
    
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return {
            "location": location,
            "error": f"Failed to fetch weather: {str(e)}"
        }

