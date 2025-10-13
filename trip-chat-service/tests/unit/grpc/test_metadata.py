from importlib.metadata import PackageNotFoundError

import grpc
import pytest
import pytest_asyncio
import pytest_mock
from tripsphere.chat import metadata_pb2, metadata_pb2_grpc

from chat.grpc.metadata import MetadataServiceServicer


@pytest_asyncio.fixture
async def server_port():
    server = grpc.aio.server()
    metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServiceServicer(), server
    )
    port = server.add_insecure_port("[::]:0")
    await server.start()
    yield port
    await server.stop(5)


@pytest_asyncio.fixture
async def channel(server_port: int):
    channel = grpc.aio.insecure_channel(f"localhost:{server_port}")
    yield channel
    await channel.close()


@pytest.mark.asyncio
async def test_get_version_success(
    channel: grpc.aio.Channel, mocker: pytest_mock.MockerFixture
):
    mocked_version = "3.1.4"
    mocker.patch("chat.grpc.metadata.version", return_value=mocked_version)
    stub = metadata_pb2_grpc.MetadataServiceStub(channel)
    response = await stub.GetVersion(metadata_pb2.GetVersionRequest())
    assert response.version == mocked_version


@pytest.mark.asyncio
async def test_get_version_package_not_found(
    channel: grpc.aio.Channel, mocker: pytest_mock.MockerFixture
):
    mocker.patch("chat.grpc.metadata.version", side_effect=PackageNotFoundError)
    stub = metadata_pb2_grpc.MetadataServiceStub(channel)
    with pytest.raises(grpc.RpcError) as exc_info:
        await stub.GetVersion(metadata_pb2.GetVersionRequest())
    assert exc_info.value.code() == grpc.StatusCode.INTERNAL
    assert exc_info.value.details() == "Required package 'chat' is not installed"
