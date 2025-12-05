from typing import AsyncGenerator

import pytest
import pytest_mock
from a2a.client import Client, ClientEvent, ClientFactory
from a2a.types import AgentCard, Role, TaskStatus
from a2a.types import Message as A2AMessage
from a2a.types import Task as A2ATask
from a2a.types import TaskState as A2ATaskState

from chat.agent.connection import RemoteAgentConnection
from chat.utils.uuid import uuid7


@pytest.fixture
def mock_deps(
    mocker: pytest_mock.MockerFixture,
) -> tuple[pytest_mock.MockType, pytest_mock.MockType, pytest_mock.MockType]:
    mock_card = mocker.MagicMock(spec=AgentCard)
    mock_factory = mocker.MagicMock(spec=ClientFactory)
    mock_client = mocker.MagicMock(spec=Client)

    # Let the factory return the mock client
    mock_factory.create.return_value = mock_client

    return mock_card, mock_factory, mock_client


@pytest.mark.asyncio
async def test_send_message_returns_message(
    mock_deps: tuple[pytest_mock.MockType, pytest_mock.MockType, pytest_mock.MockType],
    mocker: pytest_mock.MockerFixture,
) -> None:
    card, factory, client = mock_deps
    connection = RemoteAgentConnection(card, factory)

    expected_message = A2AMessage(message_id=str(uuid7()), parts=[], role=Role.agent)

    async def mock_send_message(_: A2AMessage) -> AsyncGenerator[A2AMessage, None]:
        yield expected_message

    client.send_message.side_effect = mock_send_message

    input_message = mocker.MagicMock(spec=A2AMessage)
    result = await connection.send_message(input_message)

    assert result == expected_message
    factory.create.assert_called_once_with(card)
    client.send_message.assert_called_once_with(input_message)


@pytest.mark.asyncio
async def test_send_message_returns_completed_task(
    mock_deps: tuple[pytest_mock.MockType, pytest_mock.MockType, pytest_mock.MockType],
    mocker: pytest_mock.MockerFixture,
) -> None:
    card, factory, client = mock_deps
    connection = RemoteAgentConnection(card, factory)

    # Create a mock completed Task
    expected_task = A2ATask(
        id=str(uuid7()),
        context_id=str(uuid7()),
        status=TaskStatus(state=A2ATaskState.completed),
    )

    async def mock_send_message(_: A2AMessage) -> AsyncGenerator[ClientEvent, None]:
        yield expected_task, None

    client.send_message.side_effect = mock_send_message

    input_message = mocker.MagicMock(spec=A2AMessage)
    result = await connection.send_message(input_message)

    assert result == expected_task
    factory.create.assert_called_once_with(card)
    client.send_message.assert_called_once_with(input_message)


@pytest.mark.asyncio
async def test_send_message_raises_error_when_no_result(
    mock_deps: tuple[pytest_mock.MockType, pytest_mock.MockType, pytest_mock.MockType],
    mocker: pytest_mock.MockerFixture,
) -> None:
    card, factory, client = mock_deps
    connection = RemoteAgentConnection(card, factory)

    # Return no messages or tasks
    async def mock_send_message(_: A2AMessage) -> AsyncGenerator[None, None]:
        return
        yield  # Never reached, just to make it an async generator

    client.send_message.side_effect = mock_send_message

    input_message = mocker.MagicMock(spec=A2AMessage)
    with pytest.raises(RuntimeError, match="No Task or Message received from agent."):
        await connection.send_message(input_message)

    factory.create.assert_called_once_with(card)
    client.send_message.assert_called_once_with(input_message)


@pytest.mark.asyncio
async def test_send_message_with_multiple_events(
    mock_deps: tuple[pytest_mock.MockType, pytest_mock.MockType, pytest_mock.MockType],
    mocker: pytest_mock.MockerFixture,
) -> None:
    card, factory, client = mock_deps
    connection = RemoteAgentConnection(card, factory)

    task_id = str(uuid7())
    context_id = str(uuid7())
    tasks = [
        A2ATask(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=A2ATaskState.submitted),
        ),
        A2ATask(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=A2ATaskState.working),
        ),
        A2ATask(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=A2ATaskState.completed),
        ),
    ]

    async def mock_send_message(_: A2AMessage) -> AsyncGenerator[ClientEvent, None]:
        yield (tasks[0], None)
        yield (tasks[1], None)
        yield (tasks[2], None)

    client.send_message.side_effect = mock_send_message

    input_message = mocker.MagicMock(spec=A2AMessage)
    result = await connection.send_message(input_message)

    assert result == tasks[2]
    factory.create.assert_called_once_with(card)
    client.send_message.assert_called_once_with(input_message)
