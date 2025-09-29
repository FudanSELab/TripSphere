import argparse
import logging
from concurrent import futures

import grpc
from tripsphere.itinerary import metadata_pb2_grpc

from itinerary.services.metadata import MetadataServiceServicer

logger = logging.getLogger(__name__)


def serve(port: int) -> None:
    server = grpc.server(futures.ThreadPoolExecutor(10))
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Start gRPC server on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    serve(args.port)
