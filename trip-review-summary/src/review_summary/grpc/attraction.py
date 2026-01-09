import grpc
from tripsphere.attraction.attraction_pb2 import (
    FindIdByNameRequest,
    FindIdByNameResponse,
)
from tripsphere.attraction.attraction_pb2_grpc import AttractionServiceStub

from review_summary.config.settings import get_settings


def find_attraction_id_by_name(name: str) -> str:
    settings = get_settings()
    host = settings.attraction.host
    port = settings.attraction.port
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = AttractionServiceStub(channel)

    request = FindIdByNameRequest(name=name)

    response: FindIdByNameResponse = stub.FindIdByName(request)

    return response.attraction_id
