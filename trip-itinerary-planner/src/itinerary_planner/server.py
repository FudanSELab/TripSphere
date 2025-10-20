import asyncio
import logging

import grpc
from tripsphere.itinerary import itinerary_pb2_grpc, metadata_pb2_grpc

from itinerary_planner.config.settings import settings
from itinerary_planner.grpc.metadata import MetadataServiceServicer
from itinerary_planner.grpc.planner import ItineraryPlannerServiceServicer
from itinerary_planner.nacos.client import NacosNaming

logger = logging.getLogger(__name__)


async def serve(port: int) -> None:
    server = grpc.aio.server()

    # Add servicers
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    itinerary_pb2_grpc.add_ItineraryPlannerServiceServicer_to_server(
        ItineraryPlannerServiceServicer(), server
    )

    server.add_insecure_port(f"[::]:{port}")

    # Initialize Nacos naming if enabled
    nacos_naming = None
    if settings.nacos.enabled:
        try:
            nacos_naming = await NacosNaming.create_naming()
            logger.info("Nacos service discovery enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Nacos: {e}")
            logger.warning("Continuing without service registration...")
    else:
        logger.info("Nacos service discovery disabled")

    logger.info(f"Starting gRPC server on port {port}")
    await server.start()

    # Register with Nacos if available
    if nacos_naming:
        logger.info("Registering instance with Nacos...")
        await nacos_naming.register(ephemeral=True)

    try:
        # Keep the gRPC server running
        await server.wait_for_termination()
    finally:
        # Deregister from Nacos if registered
        if nacos_naming:
            logger.info("Deregistering instance from Nacos...")
            try:
                await nacos_naming.deregister(ephemeral=True)
            except Exception as e:
                logger.warning(f"Failed to deregister from Nacos: {e}")

        logger.info("Stopping gRPC server...")
        await server.stop(5)


if __name__ == "__main__":
    fmt = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    asyncio.run(serve(settings.grpc.port))
