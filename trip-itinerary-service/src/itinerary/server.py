import asyncio
import logging

import grpc
from tripsphere.itinerary import metadata_pb2_grpc

from itinerary.config.logging import setup_logging
from itinerary.config.settings import get_settings
from itinerary.grpc.metadata import MetadataServiceServicer
from itinerary.nacos.naming import NacosNaming

setup_logging()

logger = logging.getLogger(__name__)


async def serve() -> None:
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")

    server = grpc.aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    
    server.add_insecure_port(f"[::]:{settings.grpc.port}")
    nacos_naming = await NacosNaming.create_naming(
        service_name=settings.app.name,
        port=settings.grpc.port,
        server_address=settings.nacos.server_address,
        namespace_id=settings.nacos.namespace_id,
    )

    logger.info(f"Starting gRPC server on port {settings.grpc.port}")
    await server.start()
    logger.info("Registering service instance...")
    await nacos_naming.register(ephemeral=True)

    try:
        logger.info("Itinerary service is running.")
        # Keep the gRPC server running
        await server.wait_for_termination()
    finally:
        logger.info("Deregistering service instance...")
        await nacos_naming.deregister(ephemeral=True)
        logger.info("Stopping gRPC server...")
        await server.stop(5)


if __name__ == "__main__":
    asyncio.run(serve())
