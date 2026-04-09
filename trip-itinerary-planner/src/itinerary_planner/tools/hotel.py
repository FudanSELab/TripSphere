import logging

import grpc
from pydantic import BaseModel, Field
from tripsphere.common.v1 import map_pb2
from tripsphere.hotel.v1 import hotel_pb2, hotel_pb2_grpc

from itinerary_planner.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)


class HotelDetail(BaseModel):
    id: str = Field(description="Hotel ID")
    name: str = Field(description="Hotel name")
    name_en: str = Field(description="Hotel name in English")
    poi_id: str = Field(description="Point of Interest ID")
    address: str = Field(description="Full address")
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    tags: list[str] = Field(
        default_factory=list, description="Soft tags (e.g., ['拍照出片', '氛围浪漫'])"
    )
    images: list[str] = Field(default_factory=list, description="Image URLs")
    introduction: str = Field(description="Hotel introduction/description")
    estimated_price: float | None = Field(
        default=None, description="Estimated price per night, if available"
    )
    amenities: list[str] = Field(
        default_factory=list, description="Amenities (e.g., ['健身房', '游泳池'])"
    )


class HotelSearchResult(BaseModel):
    hotels: list[HotelDetail] = Field(description="List of hotels found")


async def search_hotels_nearby(
    nacos_naming: NacosNaming,
    center_longitude: float,
    center_latitude: float,
    radius_km: float = 5.0,
    limit: int = 10,
) -> HotelSearchResult:
    """Search for hotels near a location using gRPC HotelService."""
    logger.info(
        "Searching hotels near (%.4f, %.4f) within %.1fkm, limit: %d",
        center_longitude,
        center_latitude,
        radius_km,
        limit,
    )

    instance = await nacos_naming.get_service_instance("trip-hotel-service")
    ip = instance.ip
    port = instance.metadata["gRPC_port"]  # pyright: ignore

    location = map_pb2.GeoPoint(latitude=center_latitude, longitude=center_longitude)
    request = hotel_pb2.GetHotelsNearbyRequest(
        location=location, radius_meters=radius_km * 1000
    )
    async with grpc.aio.insecure_channel(f"{ip}:{port}") as channel:
        stub = hotel_pb2_grpc.HotelServiceStub(channel)
        response = await stub.GetHotelsNearby(request)

    hotel_details: list[HotelDetail] = []
    for hotel in response.hotels[:limit]:
        # Compose full address if possible
        try:
            addr = hotel.address
            address_str = ", ".join(
                filter(
                    None,
                    [
                        getattr(addr, "province", None),
                        getattr(addr, "city", None),
                        getattr(addr, "district", None),
                        getattr(addr, "detailed", None),
                    ],
                )
            )
        except Exception:
            address_str = ""
        try:
            lat = hotel.location.latitude
            lon = hotel.location.longitude
        except Exception:
            lat = 0.0
            lon = 0.0
        # Estimated price (Money proto - value/units)
        estimated_price = None
        if hasattr(hotel, "estimated_price") and hasattr(
            hotel.estimated_price, "units"
        ):
            try:
                estimated_price = float(hotel.estimated_price.units or 0)
                if (
                    hasattr(hotel.estimated_price, "nanos")
                    and hotel.estimated_price.nanos
                ):
                    estimated_price += hotel.estimated_price.nanos / 1e9
            except Exception:
                estimated_price = None
        hotel_details.append(
            HotelDetail(
                id=hotel.id,
                name=hotel.name,
                name_en=getattr(hotel, "name_en", ""),
                poi_id=getattr(hotel, "poi_id", ""),
                address=address_str,
                latitude=lat,
                longitude=lon,
                tags=list(hotel.tags) if hasattr(hotel, "tags") else [],
                images=list(hotel.images) if hasattr(hotel, "images") else [],
                introduction=getattr(hotel, "information", None)
                and getattr(hotel.information, "introduction", "")
                or "",
                estimated_price=estimated_price,
                amenities=list(hotel.amenities) if hasattr(hotel, "amenities") else [],
            )
        )

    return HotelSearchResult(hotels=hotel_details)
