import logging

import grpc
from langchain.tools import tool  # pyright: ignore
from pydantic import BaseModel, Field
from tripsphere.attraction.v1 import attraction_pb2, attraction_pb2_grpc
from tripsphere.common.v1 import map_pb2

from itinerary_planner.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)


class AttractionDetail(BaseModel):
    id: str = Field(description="Attraction ID")
    name: str = Field(description="Attraction name")
    description: str = Field(description="Detailed description")
    longitude: float = Field(description="Longitude coordinate")
    latitude: float = Field(description="Latitude coordinate")
    address: str = Field(description="Full address")
    tags: list[str] = Field(default_factory=list, description="Tags/categories")


class AttractionSearchResult(BaseModel):
    attractions: list[AttractionDetail] = Field(description="List of attractions found")


@tool
async def search_attractions_nearby(
    nacos_naming: NacosNaming,
    center_longitude: float,
    center_latitude: float,
    radius_km: float = 20.0,
    tags: list[str] | None = None,
    limit: int = 50,
) -> AttractionSearchResult:
    """Search for attractions near a location using gRPC AttractionService.

    Arguments:
        center_longitude: Center point longitude
        center_latitude: Center point latitude
        radius_km: Search radius in kilometers (default: 20km)
        tags: Filter by tags (e.g., ["cultural", "museum", "food"])
        limit: Maximum number of results (default: 50)

    Returns:
        AttractionSearchResult with matching attractions sorted by distance
    """
    logger.info(
        f"Searching attractions near ({center_longitude}, {center_latitude}) "
        f"within {radius_km}km, tags: {tags}, limit: {limit}"
    )

    instance = await nacos_naming.get_service_instance("trip-attraction-service")
    ip = instance.ip
    port = instance.metadata["gRPC_port"]  # pyright: ignore

    location = map_pb2.GeoPoint(latitude=center_latitude, longitude=center_longitude)
    request = attraction_pb2.GetAttractionsNearbyRequest(
        location=location, radius_meters=radius_km * 1000
    )
    async with grpc.aio.insecure_channel(f"{ip}:{port}") as channel:
        stub = attraction_pb2_grpc.AttractionServiceStub(channel)
        response = await stub.GetAttractionsNearby(request)

    attractions = response.attractions
    attraction_details: list[AttractionDetail] = []
    for attraction in attractions:
        attraction_detail = AttractionDetail(
            id=attraction.id,
            name=attraction.name,
            description=attraction.introduction,
            latitude=attraction.location.latitude,
            longitude=attraction.location.longitude,
            address=(
                f"{attraction.address.province}, "
                f"{attraction.address.city}, {attraction.address.district}, "
                f"{attraction.address.detailed}"
            ),
            tags=list[str](attraction.tags),
        )
        attraction_details.append(attraction_detail)

    return AttractionSearchResult(attractions=attraction_details)


@tool
async def get_attraction_details(attraction_id: str) -> AttractionDetail:
    """Get detailed information about a specific attraction.

    Arguments:
        attraction_id: The attraction ID to fetch details for

    Returns:
        AttractionDetail with complete attraction information
    """
    logger.info(f"Fetching details for attraction: {attraction_id}")

    raise NotImplementedError
