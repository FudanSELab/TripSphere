import asyncio
import logging

import grpc
from tripsphere.chat import metadata_pb2_grpc, session_pb2_grpc

from chat.config.settings import settings
from chat.grpc.metadata import MetadataServiceServicer
from chat.grpc.session import SessionServiceServicer
from chat.nacos.client import NacosNaming

logger = logging.getLogger(__name__)


async def serve(port: int) -> None:
    server = grpc.aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    session_pb2_grpc.add_SessionServiceServicer_to_server(
        SessionServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")

    nacos_naming = await NacosNaming.create_naming()

    logger.info(f"Starting gRPC server on port {port}")
    await server.start()
    logger.info("Registering service instance...")
    await nacos_naming.register(ephemeral=True)

    try:
        logger.info("Everything is ready. Chat service is running.")
        # Keep the gRPC server running
        await server.wait_for_termination()
    finally:
        logger.info("Deregistering service instance...")
        await nacos_naming.deregister(ephemeral=True)
        logger.info("Stopping gRPC server...")
        await server.stop(5)


if __name__ == "__main__":
    fmt = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    asyncio.run(serve(settings.grpc.port))
