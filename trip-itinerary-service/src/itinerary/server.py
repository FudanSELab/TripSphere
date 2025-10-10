import asyncio
import logging

import grpc
from tripsphere.itinerary import metadata_pb2_grpc

from itinerary.grpc.metadata import MetadataServiceServicer

logger = logging.getLogger(__name__)


async def serve(port: int) -> None:
    server = grpc.aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Start gRPC server on port {port}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve(50051))
