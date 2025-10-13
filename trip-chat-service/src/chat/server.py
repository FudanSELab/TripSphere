import asyncio
import logging

import grpc
from tripsphere.chat import metadata_pb2_grpc

from chat.config.settings import settings
from chat.grpc.metadata import MetadataServiceServicer
from chat.nacos.client import NacosNaming

logger = logging.getLogger(__name__)


async def serve(port: int) -> None:
    server = grpc.aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")

    nacos_naming = NacosNaming()

    logger.info(f"Starting gRPC server on port {port}")
    await server.start()
    logger.info("Registering instance with Nacos...")
    await nacos_naming.register()

    try:
        # Keep the gRPC server running
        await server.wait_for_termination()
    finally:
        logger.info("Deregistering instance from Nacos...")
        await nacos_naming.deregister()
        logger.info("Stopping gRPC server...")
        await server.stop(5)


if __name__ == "__main__":
    fmt = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    asyncio.run(serve(settings.grpc.port))
