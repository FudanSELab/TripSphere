import logging

import grpc
import tripsphere.attraction.attraction_pb2 as attraction__pb2
import tripsphere.attraction.attraction_pb2_grpc as attraction__pb2_grpc

logger = logging.getLogger(__name__)


async def find_attraction_id_by_name(
    name: str, host: str = "127.0.0.1", port: int = 9007
) -> str:
    # Nacos service discovery would go here (omitted for brevity)
    # TODO

    # Create an insecure channel (development)
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = attraction__pb2_grpc.AttractionServiceStub(channel)
        request = attraction__pb2.FindIdByNameRequest(name=name)
        response = stub.FindIdByName(request)
        return response.attraction_id
