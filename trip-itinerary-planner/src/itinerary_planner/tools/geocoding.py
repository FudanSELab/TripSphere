"""Geocoding tool — shared by workflow and chat agent (single @tool)."""

import logging

from httpx import AsyncClient
from langchain_core.tools import tool
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
        city: Optional city context (e.g., "Shanghai", "Beijing")

    Returns:
        GeocodeResult with coordinates and address information
    Use when the user asks for coordinates or address of a place.
    """
    logger.info("Geocoding: %s (city: %s)", address, city)

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
                latitude=float(latitude),
                longitude=float(longitude),
                address=data["geocodes"][0]["formatted_address"],
            )
        else:
            logger.error("Geocoding failed: %s", data["info"])
            raise ValueError(f"Geocoding failed: {data['info']}")
