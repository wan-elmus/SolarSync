import requests
from app.core.config import config
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """
    Geocode an address using the Google Maps Geocoding API.

    Args:
        address (str): The address to geocode (e.g., "123 Main St, Nairobi, Kenya").

    Returns:
        Optional[Dict[str, float]]: A dictionary with 'lat' and 'lon' coordinates if successful, None otherwise.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": config.GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK":
            logger.error(f"Geocoding failed for address '{address}': {data['status']}")
            return None

        location = data["results"][0]["geometry"]["location"]
        coordinates = {
            "lat": location["lat"],
            "lon": location["lng"]
        }
        logger.info(f"Geocoded address '{address}' to coordinates: {coordinates}")
        return coordinates

    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {str(e)}")
        return None

def calculate_distance(origin: Dict[str, float], destination: Dict[str, float]) -> Optional[float]:
    """
    Calculate the distance between two coordinates using the Google Maps Distance Matrix API.

    Args:
        origin (Dict[str, float]): The origin coordinates (e.g., {"lat": -1.2699, "lon": 36.8408}).
        destination (Dict[str, float]): The destination coordinates.

    Returns:
        Optional[float]: The distance in kilometers if successful, None otherwise.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{origin['lat']},{origin['lon']}",
            "destinations": f"{destination['lat']},{destination['lon']}",
            "key": config.GOOGLE_MAPS_API_KEY,
            "units": "metric"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK":
            logger.error(f"Distance calculation failed: {data['status']}")
            return None

        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            logger.error(f"Distance calculation failed for element: {element['status']}")
            return None

        distance_km = element["distance"]["value"] / 1000.0  # Convert meters to kilometers
        logger.info(f"Calculated distance between {origin} and {destination}: {distance_km} km")
        return distance_km

    except Exception as e:
        logger.error(f"Error calculating distance between {origin} and {destination}: {str(e)}")
        return None