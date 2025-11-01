from importlib.metadata import PackageNotFoundError
from typing import AsyncGenerator

import grpc
import pytest
import pytest_asyncio
import pytest_mock
from grpc.aio import AioRpcError
from tripsphere.chat import metadata_pb2

from chat.grpc.servicers.metadata import MetadataServiceServicer


@pytest_asyncio.fixture
async def servicer() -> AsyncGenerator[MetadataServiceServicer, None]:
    servicer = MetadataServiceServicer()
    yield servicer


@pytest.mark.asyncio
async def test_get_version_success(
    servicer: MetadataServiceServicer, mocker: pytest_mock.MockerFixture
) -> None:
    mocked_version = "3.14.0"
    mocker.patch("chat.grpc.servicers.metadata.version", return_value=mocked_version)
    context = mocker.Mock()
    response = await servicer.GetVersion(metadata_pb2.GetVersionRequest(), context)
    assert response.version == mocked_version


@pytest.mark.asyncio
async def test_get_version_package_not_found(
    servicer: MetadataServiceServicer, mocker: pytest_mock.MockerFixture
) -> None:
    mocker.patch(
        "chat.grpc.servicers.metadata.version", side_effect=PackageNotFoundError
    )
    context = mocker.Mock()
    context.abort = mocker.AsyncMock(
        side_effect=AioRpcError(
            code=grpc.StatusCode.INTERNAL,
            initial_metadata=mocker.Mock(),
            trailing_metadata=mocker.Mock(),
            details="Required package 'chat' is not installed",
        )
    )
    with pytest.raises(grpc.RpcError) as exc_info:
        await servicer.GetVersion(metadata_pb2.GetVersionRequest(), context)
    assert exc_info.value.code() == grpc.StatusCode.INTERNAL
    assert exc_info.value.details() == "Required package 'chat' is not installed"
