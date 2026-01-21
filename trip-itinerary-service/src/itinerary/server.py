import logging
from typing import Any

import grpc
from httpx import AsyncClient
from pymongo import AsyncMongoClient
from tripsphere.itinerary import (
    itinerary_pb2_grpc,
    metadata_pb2_grpc,
    planning_pb2_grpc,
)

from itinerary.config.logging import setup_logging
from itinerary.config.settings import get_settings
from itinerary.grpc.itinerary import ItineraryServiceServicer
from itinerary.grpc.metadata import MetadataServiceServicer
from itinerary.grpc.planning import PlanningServiceServicer
from itinerary.itinerary.repositories import MongoItineraryRepository
from itinerary.nacos.ai import NacosAI
from itinerary.nacos.naming import NacosNaming
from itinerary.nacos.utils import client_shutdown

logger = logging.getLogger(__name__)

setup_logging()


async def serve() -> None:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    # Create gRPC server
    server = grpc.aio.server()
    server.add_insecure_port(f"[::]:{settings.grpc.port}")

    logger.info(f"Connecting to MongoDB at {settings.mongo.uri}")
    mongo_client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
    database = mongo_client[settings.mongo.database]
    collection = database[MongoItineraryRepository.COLLECTION_NAME]
    itinerary_repository = MongoItineraryRepository(collection)

    httpx_client: AsyncClient = AsyncClient()
    nacos_ai: NacosAI | None = None
    nacos_naming: NacosNaming | None = None

    try:
        nacos_naming = await NacosNaming.create_naming(
            service_name=settings.app.name,
            port=settings.grpc.port,
            server_address=settings.nacos.server_address,
            namespace_id=settings.nacos.namespace_id,
        )
        nacos_ai = await NacosAI.create_nacos_ai(
            server_address=settings.nacos.server_address
        )

        metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
            MetadataServiceServicer(), server
        )
        planning_pb2_grpc.add_PlanningServiceServicer_to_server(
            PlanningServiceServicer(httpx_client, itinerary_repository, nacos_ai),
            server,
        )
        itinerary_pb2_grpc.add_ItineraryServiceServicer_to_server(
            ItineraryServiceServicer(itinerary_repository), server
        )

        logger.info(f"Starting gRPC server on port {settings.grpc.port}")
        await server.start()

        logger.info("Registering service instance...")
        await nacos_naming.register(ephemeral=True)

        logger.info("Itinerary service is running.")
        # Block to keep the gRPC server running
        await server.wait_for_termination()

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

    finally:
        logger.info("Deregistering service instance...")
        if isinstance(nacos_naming, NacosNaming):
            await nacos_naming.deregister(ephemeral=True)

        logger.info("Stopping gRPC aio server...")
        await server.stop(5)

        logger.info("Shutting down Nacos client...")
        await client_shutdown(nacos_ai, nacos_naming)

        await httpx_client.aclose()

        logger.info("Closing MongoDB connection...")
        await mongo_client.close()
