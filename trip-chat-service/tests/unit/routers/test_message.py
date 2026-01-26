from datetime import datetime
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import AsyncMockType, MockerFixture

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_httpx_client,
    provide_message_repository,
    provide_mongo_client,
    provide_nacos_ai,
)
from chat.common.parts import Part, TextPart
from chat.internal.manager import ConversationManager
from chat.internal.models import Author, Conversation, Message
from chat.internal.repository import ConversationRepository, MessageRepository
from chat.routers.message import messages
from chat.utils.pagination import CursorPagination


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI application for testing."""
    app = FastAPI()
    app.include_router(messages, prefix="/api/v1")
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_conversation_repository(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock ConversationRepository."""
    mock_conversation_repository = mocker.AsyncMock(spec=ConversationRepository)

    def override_provide_conversation_repository() -> AsyncMockType:
        return cast(AsyncMockType, mock_conversation_repository)

    app.dependency_overrides[provide_conversation_repository] = (
        override_provide_conversation_repository
    )
    return cast(AsyncMockType, mock_conversation_repository)


@pytest.fixture
def mock_message_repository(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock MessageRepository."""
    mock_message_repository = mocker.AsyncMock(spec=MessageRepository)

    def override_provide_message_repository() -> AsyncMockType:
        return cast(AsyncMockType, mock_message_repository)

    app.dependency_overrides[provide_message_repository] = (
        override_provide_message_repository
    )
    return cast(AsyncMockType, mock_message_repository)


@pytest.fixture
def mock_conversation_manager(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock ConversationManager."""
    mock_conversation_manager = mocker.AsyncMock(spec=ConversationManager)

    def override_provide_conversation_manager() -> AsyncMockType:
        return cast(AsyncMockType, mock_conversation_manager)

    app.dependency_overrides[provide_conversation_manager] = (
        override_provide_conversation_manager
    )
    return cast(AsyncMockType, mock_conversation_manager)


@pytest.fixture
def mock_httpx_client(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock AsyncClient for httpx."""
    mock_client = mocker.AsyncMock()

    def override_provide_httpx_client() -> AsyncMockType:
        return cast(AsyncMockType, mock_client)

    app.dependency_overrides[provide_httpx_client] = override_provide_httpx_client
    return cast(AsyncMockType, mock_client)


@pytest.fixture
def mock_mongo_client(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock AsyncMongoClient."""
    mock_client = mocker.AsyncMock()

    def override_provide_mongo_client() -> AsyncMockType:
        return cast(AsyncMockType, mock_client)

    app.dependency_overrides[provide_mongo_client] = override_provide_mongo_client
    return cast(AsyncMockType, mock_client)


@pytest.fixture
def mock_nacos_naming(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock NacosNaming."""
    mock_naming = mocker.AsyncMock()

    def override_provide_nacos_ai() -> AsyncMockType:
        return cast(AsyncMockType, mock_naming)

    app.dependency_overrides[provide_nacos_ai] = override_provide_nacos_ai
    return cast(AsyncMockType, mock_naming)


@pytest.fixture
def sample_conversation() -> Conversation:
    """Create a sample Conversation for testing."""
    return Conversation(
        _id="conv-123",
        title="Test Conversation",
        user_id="user-456",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        metadata={"key": "value"},
    )


@pytest.fixture
def sample_message() -> Message:
    """Create a sample Message for testing."""
    return Message(
        _id="msg-123",
        conversation_id="conv-123",
        author=Author.user(name="Test User"),
        content=[Part(root=TextPart(text="Hello, world!"))],
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        metadata={"key": "value"},
    )


@pytest.fixture
def sample_messages() -> list[Message]:
    """Create multiple sample Messages for testing."""
    return [
        Message(
            _id=f"msg-{i}",
            conversation_id="conv-123",
            author=Author.user(name="Test User"),
            content=[Part(root=TextPart(text=f"Message {i}"))],
            created_at=datetime(2025, 1, i, 12, 0, 0),
            metadata={"index": i},
        )
        for i in range(1, 4)
    ]


class TestStreamMessage:
    """Test cases for POST /api/v1/messages/stream endpoint."""

    def test_stream_message_conversation_not_found(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_message_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        mock_httpx_client: AsyncMockType,
        mock_mongo_client: AsyncMockType,
        mock_nacos_naming: AsyncMockType,
    ) -> None:
        """Test streaming message when conversation is not found."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = None

        # Act
        response = client.post(
            "/api/v1/messages/stream",
            json={
                "conversation_id": "non-existent",
                "content": [{"text": "Hello", "kind": "text"}],
            },
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["message"].lower()

        mock_find_by_id.assert_called_once_with("non-existent")

    def test_stream_message_access_denied(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_message_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
        mock_httpx_client: AsyncMockType,
        mock_mongo_client: AsyncMockType,
        mock_nacos_naming: AsyncMockType,
    ) -> None:
        """Test streaming message when user does not own the conversation."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        # Act
        response = client.post(
            "/api/v1/messages/stream",
            json={
                "conversation_id": "conv-123",
                "content": [{"text": "Hello", "kind": "text"}],
            },
            headers={"x-user-id": "different-user"},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not authorized" in data["detail"]["message"].lower()

        mock_find_by_id.assert_called_once_with("conv-123")

    def test_stream_message_missing_user_header(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_message_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        mock_httpx_client: AsyncMockType,
        mock_mongo_client: AsyncMockType,
        mock_nacos_naming: AsyncMockType,
    ) -> None:
        """Test streaming message without x-user-id header."""
        # Act
        response = client.post(
            "/api/v1/messages/stream",
            json={
                "conversation_id": "conv-123",
                "content": [{"text": "Hello", "kind": "text"}],
            },
            headers={},
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_stream_message_invalid_content(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_message_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
        mock_httpx_client: AsyncMockType,
        mock_mongo_client: AsyncMockType,
        mock_nacos_naming: AsyncMockType,
    ) -> None:
        """Test streaming message with invalid content format."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        # Act
        response = client.post(
            "/api/v1/messages/stream",
            json={"conversation_id": "conv-123", "content": "invalid"},
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestGetMessage:
    """Test cases for GET /api/v1/messages/{message_id} endpoint."""

    def test_get_message_success(
        self,
        client: TestClient,
        mock_message_repository: AsyncMockType,
        mock_conversation_repository: AsyncMockType,
        sample_message: Message,
        sample_conversation: Conversation,
    ) -> None:
        """Test successfully retrieving a message."""
        # Arrange
        mock_find_message: AsyncMockType = mock_message_repository.find_by_id
        mock_find_message.return_value = sample_message
        mock_find_conversation: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_conversation.return_value = sample_conversation

        # Act
        response = client.get(
            "/api/v1/messages/msg-123", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "msg-123"
        assert data["conversation_id"] == "conv-123"
        assert data["author"]["role"] == "user"
        assert len(data["content"]) == 1

        mock_find_message.assert_called_once_with("msg-123")
        mock_find_conversation.assert_called_once_with("conv-123")

    def test_get_message_not_found(
        self,
        client: TestClient,
        mock_message_repository: AsyncMockType,
        mock_conversation_repository: AsyncMockType,
    ) -> None:
        """Test retrieving a non-existent message."""
        # Arrange
        mock_find_message: AsyncMockType = mock_message_repository.find_by_id
        mock_find_message.return_value = None

        # Act
        response = client.get(
            "/api/v1/messages/non-existent", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["message"].lower()

    def test_get_message_access_denied(
        self,
        client: TestClient,
        mock_message_repository: AsyncMockType,
        mock_conversation_repository: AsyncMockType,
        sample_message: Message,
        sample_conversation: Conversation,
    ) -> None:
        """Test retrieving a message from conversation user does not own."""
        # Arrange
        mock_find_message: AsyncMockType = mock_message_repository.find_by_id
        mock_find_message.return_value = sample_message
        mock_find_conversation: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_conversation.return_value = sample_conversation

        # Act
        response = client.get(
            "/api/v1/messages/msg-123", headers={"x-user-id": "different-user"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not authorized" in data["detail"]["message"].lower()

    def test_get_message_conversation_not_found(
        self,
        client: TestClient,
        mock_message_repository: AsyncMockType,
        mock_conversation_repository: AsyncMockType,
        sample_message: Message,
    ) -> None:
        """Test retrieving a message when its conversation does not exist."""
        # Arrange
        mock_find_message: AsyncMockType = mock_message_repository.find_by_id
        mock_find_message.return_value = sample_message
        mock_find_conversation: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_conversation.return_value = None

        # Act
        response = client.get(
            "/api/v1/messages/msg-123", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["message"].lower()

    def test_get_message_missing_user_header(
        self,
        client: TestClient,
        mock_message_repository: AsyncMockType,
        mock_conversation_repository: AsyncMockType,
    ) -> None:
        """Test retrieving a message without x-user-id header."""
        # Arrange

        # Act
        response = client.get("/api/v1/messages/msg-123", headers={})

        # Assert
        assert response.status_code == 422  # Validation error


class TestListConversationMessages:
    """Test cases for GET /api/v1/messages endpoint."""

    def test_list_messages_success(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
        sample_messages: list[Message],
    ) -> None:
        """Test successfully listing conversation messages."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        pagination = CursorPagination[str, Message](
            items=sample_messages,
            results_per_page=10,
            cursor=None,
        )
        mock_list_messages: AsyncMockType = (
            mock_conversation_manager.list_conversation_messages
        )
        mock_list_messages.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123&results_per_page=10",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["results_per_page"] == 10
        assert data["cursor"] is None

        mock_find_by_id.assert_called_once_with("conv-123")
        mock_list_messages.assert_called_once_with(
            sample_conversation, 10, direction="backward", cursor=None
        )

    def test_list_messages_with_cursor(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
        sample_messages: list[Message],
    ) -> None:
        """Test listing messages with pagination cursor."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        pagination = CursorPagination[str, Message](
            items=sample_messages[:2],
            results_per_page=2,
            cursor="another-cursor",
        )
        mock_list_messages: AsyncMockType = (
            mock_conversation_manager.list_conversation_messages
        )
        mock_list_messages.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123&results_per_page=2&cursor=prev-cursor",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["cursor"] == "another-cursor"

        mock_list_messages.assert_called_once_with(
            sample_conversation, 2, direction="backward", cursor="prev-cursor"
        )

    def test_list_messages_empty_result(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test listing messages with no results."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        pagination = CursorPagination[str, Message](
            items=[], results_per_page=10, cursor=None
        )
        mock_list_messages: AsyncMockType = (
            mock_conversation_manager.list_conversation_messages
        )
        mock_list_messages.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123&results_per_page=10",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["cursor"] is None

    def test_list_messages_conversation_not_found(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
    ) -> None:
        """Test listing messages when conversation does not exist."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = None

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=non-existent&results_per_page=10",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["message"].lower()

    def test_list_messages_access_denied(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test listing messages when user does not own the conversation."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123&results_per_page=10",
            headers={"x-user-id": "different-user"},
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not authorized" in data["detail"]["message"].lower()

    def test_list_messages_missing_conversation_id(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
    ) -> None:
        """Test listing messages without conversation_id parameter."""
        # Arrange

        # Act
        response = client.get(
            "/api/v1/messages?results_per_page=10", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_list_messages_missing_results_per_page(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test listing messages without results_per_page parameter."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_list_messages_missing_user_header(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
    ) -> None:
        """Test listing messages without x-user-id header."""
        # Arrange

        # Act
        response = client.get(
            "/api/v1/messages?conversation_id=conv-123&results_per_page=10",
            headers={},
        )

        # Assert
        assert response.status_code == 422  # Validation error
