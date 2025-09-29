from concurrent import futures
from importlib.metadata import PackageNotFoundError
from typing import Generator

import grpc
import pytest
import pytest_mock
from tripsphere.itinerary import metadata_pb2, metadata_pb2_grpc

from itinerary.services.metadata import MetadataServiceServicer


@pytest.fixture(scope="module")
def server_port() -> Generator[int, None, None]:
    server = grpc.server(futures.ThreadPoolExecutor(10))
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    port = server.add_insecure_port("[::]:0")
    server.start()
    yield port
    server.stop(5)


@pytest.fixture(scope="module")
def channel(server_port: int) -> Generator[grpc.Channel, None, None]:
    channel = grpc.insecure_channel(f"localhost:{server_port}")
    yield channel
    channel.close()


def test_get_version_success(
    channel: grpc.Channel, mocker: pytest_mock.MockerFixture
) -> None:
    mocked_version = "1.0.0"
    mocker.patch("itinerary.services.metadata.version", return_value=mocked_version)
    stub = metadata_pb2_grpc.MetadataServiceStub(channel)
    response = stub.GetVersion(metadata_pb2.GetVersionRequest())
    assert response.version == mocked_version


def test_get_version_package_not_found(
    channel: grpc.Channel, mocker: pytest_mock.MockerFixture
) -> None:
    mocker.patch(
        "itinerary.services.metadata.version", side_effect=PackageNotFoundError
    )
    stub = metadata_pb2_grpc.MetadataServiceStub(channel)
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.GetVersion(metadata_pb2.GetVersionRequest())
    assert exc_info.value.code() == grpc.StatusCode.INTERNAL
    assert exc_info.value.details() == "Required package 'itinerary' is not installed"
