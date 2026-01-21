import logging

from httpx import AsyncClient
from langchain_core.tools import tool  # pyright: ignore
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GeocodeResult(BaseModel):
    """Result of geocoding a location."""

    name: str = Field(description="Location name")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    address: str = Field(description="Full address or description")


@tool
async def geocoding_tool(address: str, city: str = "") -> GeocodeResult:
    """Convert a location name to geographic coordinates (latitude, longitude).

    Arguments:
        address: Name or address of the location to geocode
        (e.g., "Shanghai", "Beijing", "Hangzhou", "Nanjing", "Suzhou")
        city: Optional city context (e.g., "Shanghai", "Beijing")

    Returns:
        GeocodeResult with coordinates and address information
    """
    logger.info(f"Geocoding: {address} (city: {city})")

    endpoint = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": "90b08d9c9b136bf3543d05181b86cf5c",
        "address": address,
        "city": city,
    }
    async with AsyncClient() as client:
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "1" and data["infocode"] == "10000":
            longitude, latitude = data["geocodes"][0]["location"].split(",")
            return GeocodeResult(
                name=data["geocodes"][0]["formatted_address"],
                latitude=latitude,
                longitude=longitude,
                address=data["geocodes"][0]["formatted_address"],
            )
        else:
            logger.error(f"Geocoding failed: {data['info']}")
            raise ValueError(f"Geocoding failed: {data['info']}")

    # MOCK DATA - Replace with actual API call
    # This provides realistic coordinates for common Chinese cities
    mock_locations = {
        "shanghai": GeocodeResult(
            name="上海市", latitude=31.2304, longitude=121.4737, address="上海市"
        ),
        "beijing": GeocodeResult(
            name="北京市", latitude=39.9042, longitude=116.4074, address="北京市"
        ),
        "hangzhou": GeocodeResult(
            name="杭州市", latitude=30.2741, longitude=120.1551, address="浙江省杭州市"
        ),
        "nanjing": GeocodeResult(
            name="南京市", latitude=32.0603, longitude=118.7969, address="江苏省南京市"
        ),
        "suzhou": GeocodeResult(
            name="苏州市", latitude=31.2989, longitude=120.5853, address="江苏省苏州市"
        ),
    }

    # Normalize search key
    search_key = address.lower().replace(" ", "").replace(",", "")
    if city:
        search_key = city.lower().replace(" ", "")

    # Try to find mock location
    for key, location in mock_locations.items():
        if key in search_key:
            logger.info(
                f"Geocoding result (MOCK): {location.name} "
                f"({location.latitude}, {location.longitude})"
            )
            return location

    # Default fallback - use Shanghai coordinates
    logger.warning(f"No mock data for {address}, using default Shanghai coordinates")
    return GeocodeResult(
        name=address,
        latitude=31.230525,
        longitude=121.473667,
        address=f"{city if city else address}",
    )
