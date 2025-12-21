import asyncio
import logging

import grpc
import tripsphere.attraction.attraction_pb2 as attraction__pb2
import tripsphere.attraction.attraction_pb2_grpc as attraction__pb2_grpc

logger = logging.getLogger(__name__)


async def find_attraction_id_by_name(
    name: str, host: str = "127.0.0.1", port: int = 9007
) -> str:
    """
    Find the attraction ID by its name.

    Args:
        name: attraction name
        host: gRPC service host
        port: gRPC service port

    Returns:
        Attraction ID string
    """
    # Create an insecure channel (development)
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = attraction__pb2_grpc.AttractionServiceStub(channel)
        request = attraction__pb2.FindIdByNameRequest(name=name)
        response = stub.FindIdByName(request)
        return response.attraction_id


if __name__ == "__main__":
    attraction_name = "迪士尼乐园"
    attraction_id = asyncio.run(find_attraction_id_by_name(attraction_name))
    print(f"Attraction ID for '{attraction_name}': {attraction_id}")
