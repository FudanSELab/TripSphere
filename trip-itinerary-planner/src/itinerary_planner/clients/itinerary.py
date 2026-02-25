"""gRPC client for trip-itinerary-service."""

import logging

import grpc
from tripsphere.itinerary.v1 import (  # pyright: ignore
    itinerary_pb2,
    itinerary_pb2_grpc,
)

from itinerary_planner.clients.converters import itinerary_to_proto
from itinerary_planner.models.itinerary import Itinerary
from itinerary_planner.nacos.naming import NacosNaming

logger = logging.getLogger(__name__)

SERVICE_NAME = "trip-itinerary-service"


async def create_itinerary_grpc(
    nacos_naming: NacosNaming,
    user_id: str,
    itinerary: Itinerary,
) -> str:
    """Persist an itinerary via the CreateItinerary gRPC call.

    Returns:
        The server-assigned itinerary ID.
    """
    instance = await nacos_naming.get_service_instance(SERVICE_NAME)
    ip = instance.ip
    port = instance.metadata["gRPC_port"]  # pyright: ignore

    proto_itinerary = itinerary_to_proto(itinerary)
    request = itinerary_pb2.CreateItineraryRequest(itinerary=proto_itinerary)

    metadata: list[tuple[str, str]] = [
        ("x-user-id", user_id),
        ("x-user-roles", "USER"),
    ]

    logger.info("Calling CreateItinerary on %s:%s for user %s", ip, port, user_id)

    async with grpc.aio.insecure_channel(f"{ip}:{port}") as channel:
        stub = itinerary_pb2_grpc.ItineraryServiceStub(channel)
        response: itinerary_pb2.CreateItineraryResponse = await stub.CreateItinerary(
            request, metadata=metadata
        )

    persisted_id: str = response.itinerary.id
    logger.info("Itinerary persisted with id: %s", persisted_id)
    return persisted_id
