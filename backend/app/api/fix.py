import requests
from app.core.config import config
import logging
from typing import Optional
import redis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_peak_sun_hours(lat: float, lon: float) -> Optional[float]:
    """
    Fetch weather data from OpenWeatherMap and estimate peak sun hours, with Redis caching.

    Uses cloud cover to estimate peak sun hours, with a range adjusted based on latitude.

    Args:
        lat (float): Latitude of the location (-90 to 90).
        lon (float): Longitude of the location (-180 to 180).

    Returns:
        Optional[float]: Estimated peak sun hours, or None if the request fails.

    Raises:
        ValueError: If lat or lon is out of valid range.
    """
    try:
        # Validate latitude and longitude
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

        # Create a cache key based on latitude and longitude (rounded to 2 decimal places)
        cache_key = f"peak_sun_hours:{round(lat, 2)}:{round(lon, 2)}"

        # Check if the data is in Redis
        cached_value = redis_client.get(cache_key)
        if cached_value:
            logger.info(f"Cache hit for peak sun hours at lat={lat}, lon={lon}")
            return float(cached_value)

        # Use OpenWeatherMap One Call API to get current weather
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": "minutely,hourly,daily,alerts",
            "appid": config.OPENWEATHERMAP_API_KEY,
            "units": "metric"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        weather_data = response.json()

        # Check if the required data is present
        if "current" not in weather_data or "clouds" not in weather_data["current"]:
            logger.error(f"Invalid weather data response: {weather_data}")
            raise ValueError("Weather data missing 'current' or 'clouds' field")

        # Adjust peak sun hours range based on latitude
        # Near equator (lat ~0): higher max; near poles (lat ~90): lower max
        max_peak_sun_hours = 8.0 - (abs(lat) / 90) * 2.0  # 8.0 at equator, 6.0 at poles
        min_peak_sun_hours = 4.0 - (abs(lat) / 90) * 1.0  # 4.0 at equator, 3.0 at poles

        # Estimate peak sun hours based on cloud cover
        cloud_cover = weather_data["current"]["clouds"]  # 0 to 100 (%)
        peak_sun_hours = max_peak_sun_hours - (cloud_cover / 100) * (max_peak_sun_hours - min_peak_sun_hours)

        # Cache the result in Redis with a TTL of 24 hours (86400 seconds)
        redis_client.setex(cache_key, 86400, peak_sun_hours)
        logger.info(f"Cached peak sun hours {peak_sun_hours} for lat={lat}, lon={lon}")

        logger.info(f"Estimated peak_sun_hours for lat={lat}, lon={lon}: {peak_sun_hours}")
        return peak_sun_hours

    except Exception as e:
        logger.error(f"Error fetching weather data for lat={lat}, lon={lon}: {str(e)}")
        # Fallback to a latitude-based default
        default_peak_sun_hours = 6.0 - (abs(lat) / 90) * 1.5  # 6.0 at equator, 4.5 at poles
        logger.info(f"Using default peak_sun_hours: {default_peak_sun_hours}")
        return default_peak_sun_hours