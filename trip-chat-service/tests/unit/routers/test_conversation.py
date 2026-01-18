from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import AsyncMockType, MockerFixture

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
)
from chat.internal.manager import ConversationManager
from chat.internal.models import Conversation
from chat.internal.repository import ConversationRepository
from chat.routers.conversation import conversations
from chat.utils.pagination import CursorPagination


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI application for testing."""
    app = FastAPI()
    app.include_router(conversations, prefix="/api/v1")
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_conversation_manager(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock ConversationManager."""
    mock_conversation_manager = mocker.AsyncMock(spec=ConversationManager)

    def override_provide_conversation_manager() -> AsyncMockType:
        return mock_conversation_manager

    app.dependency_overrides[provide_conversation_manager] = (
        override_provide_conversation_manager
    )
    return mock_conversation_manager


@pytest.fixture
def mock_conversation_repository(app: FastAPI, mocker: MockerFixture) -> AsyncMockType:
    """Create a mock ConversationRepository."""
    mock_conversation_repository = mocker.AsyncMock(spec=ConversationRepository)

    def override_provide_conversation_repository() -> AsyncMockType:
        return mock_conversation_repository

    app.dependency_overrides[provide_conversation_repository] = (
        override_provide_conversation_repository
    )
    return mock_conversation_repository


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
def sample_conversations() -> list[Conversation]:
    """Create multiple sample Conversations for testing."""
    return [
        Conversation(
            _id=f"conv-{i}",
            title=f"Conversation {i}",
            user_id="user-456",
            created_at=datetime(2025, 1, i, 12, 0, 0),
            metadata={"index": i},
        )
        for i in range(1, 4)
    ]


class TestCreateConversation:
    """Test cases for POST /api/v1/conversations endpoint."""

    def test_create_conversation_with_title_and_metadata(
        self,
        client: TestClient,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test creating a conversation with title and metadata."""
        # Arrange
        mock_create_conversation: AsyncMockType = (
            mock_conversation_manager.create_conversation
        )
        mock_create_conversation.return_value = sample_conversation

        # Act
        response = client.post(
            "/api/v1/conversations",
            json={"title": "Test Conversation", "metadata": {"key": "value"}},
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == "conv-123"
        assert data["title"] == "Test Conversation"
        assert data["user_id"] == "user-456"
        assert data["metadata"] == {"key": "value"}

        mock_create_conversation.assert_called_once_with(
            user_id="user-456", title="Test Conversation", metadata={"key": "value"}
        )

    def test_create_conversation_with_title_only(
        self, client: TestClient, mock_conversation_manager: AsyncMockType
    ) -> None:
        """Test creating a conversation with only title."""
        # Arrange
        conversation = Conversation(
            _id="conv-789",
            title="Title Only",
            user_id="user-456",
            created_at=datetime.now(),
            metadata=None,
        )
        mock_create_conversation: AsyncMockType = (
            mock_conversation_manager.create_conversation
        )
        mock_create_conversation.return_value = conversation

        # Act
        response = client.post(
            "/api/v1/conversations",
            json={"title": "Title Only"},
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Title Only"
        assert data["metadata"] is None

        mock_create_conversation.assert_called_once_with(
            user_id="user-456", title="Title Only", metadata=None
        )

    def test_create_conversation_without_optional_fields(
        self, client: TestClient, mock_conversation_manager: AsyncMockType
    ) -> None:
        """Test creating a conversation without title or metadata."""
        # Arrange
        conversation = Conversation(
            _id="conv-999",
            title=None,
            user_id="user-456",
            created_at=datetime.now(),
            metadata=None,
        )
        mock_create_conversation: AsyncMockType = (
            mock_conversation_manager.create_conversation
        )
        mock_create_conversation.return_value = conversation

        # Act
        response = client.post(
            "/api/v1/conversations", json={}, headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None
        assert data["metadata"] is None

        mock_create_conversation.assert_called_once_with(
            user_id="user-456", title=None, metadata=None
        )

    def test_create_conversation_missing_user_header(
        self, client: TestClient, mock_conversation_manager: AsyncMockType
    ) -> None:
        """Test creating a conversation without x-user-id header."""
        # Arrange

        # Act
        response = client.post(
            "/api/v1/conversations", json={"title": "Test"}, headers={}
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestListUserConversations:
    """Test cases for GET /api/v1/conversations endpoint."""

    def test_list_conversations_success(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        sample_conversations: list[Conversation],
    ) -> None:
        """Test successfully listing user conversations."""
        # Arrange
        pagination = CursorPagination[str, Conversation](
            items=sample_conversations,
            results_per_page=10,
            cursor=None,
        )
        mock_find_by_user: AsyncMockType = mock_conversation_repository.list_by_user
        mock_find_by_user.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/conversations?results_per_page=10",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["results_per_page"] == 10
        assert data["cursor"] is None

        mock_find_by_user.assert_called_once_with(
            "user-456", limit=10, direction="backward", token=None
        )

    def test_list_conversations_with_cursor(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        sample_conversations: list[Conversation],
    ) -> None:
        """Test listing conversations with pagination cursor."""
        # Arrange
        pagination = CursorPagination[str, Conversation](
            items=sample_conversations[:2],
            results_per_page=2,
            cursor="another-cursor",
        )
        mock_find_by_user: AsyncMockType = mock_conversation_repository.list_by_user
        mock_find_by_user.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/conversations?results_per_page=2&cursor=prev-cursor",
            headers={"x-user-id": "user-456"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["cursor"] == "another-cursor"

        mock_find_by_user.assert_called_once_with(
            "user-456", limit=2, direction="backward", token="prev-cursor"
        )

    def test_list_conversations_empty_result(
        self, client: TestClient, mock_conversation_repository: AsyncMockType
    ) -> None:
        """Test listing conversations with no results."""
        # Arrange
        pagination = CursorPagination[str, Conversation](
            items=[], results_per_page=10, cursor=None
        )
        mock_find_by_user: AsyncMockType = mock_conversation_repository.list_by_user
        mock_find_by_user.return_value = pagination

        # Act
        response = client.get(
            "/api/v1/conversations?results_per_page=10",
            headers={"x-user-id": "user-789"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["cursor"] is None

        mock_find_by_user.assert_called_once_with(
            "user-789", limit=10, direction="backward", token=None
        )

    def test_list_conversations_missing_results_per_page(
        self, client: TestClient, mock_conversation_repository: AsyncMockType
    ) -> None:
        """Test listing conversations without required results_per_page parameter."""
        # Arrange

        # Act
        response = client.get(
            "/api/v1/conversations", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestDeleteConversation:
    """Test cases for DELETE /api/v1/conversations/{conversation_id} endpoint."""

    def test_delete_conversation_success(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test successfully deleting a conversation."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation
        mock_delete_conversation: AsyncMockType = (
            mock_conversation_manager.delete_conversation
        )
        mock_delete_conversation.return_value = None

        # Act
        response = client.delete(
            "/api/v1/conversations/conv-123", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 204

        mock_find_by_id.assert_called_once_with("conv-123")
        mock_delete_conversation.assert_called_once_with(sample_conversation)

    def test_delete_conversation_not_found(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
    ) -> None:
        """Test deleting a non-existent conversation."""
        # Arrange

        # Act
        response = client.delete(
            "/api/v1/conversations/non/existent", headers={"x-user-id": "user-456"}
        )

        # Assert
        assert response.status_code == 404

    def test_delete_conversation_access_denied(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
        sample_conversation: Conversation,
    ) -> None:
        """Test deleting a conversation belonging to another user."""
        # Arrange
        mock_find_by_id: AsyncMockType = mock_conversation_repository.find_by_id
        mock_find_by_id.return_value = sample_conversation

        # Act
        response = client.delete(
            "/api/v1/conversations/conv-123", headers={"x-user-id": "different-user"}
        )

        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "not authorized" in data["detail"]["message"].lower()

        mock_find_by_id.assert_called_once_with("conv-123")

    def test_delete_conversation_missing_user_header(
        self,
        client: TestClient,
        mock_conversation_repository: AsyncMockType,
        mock_conversation_manager: AsyncMockType,
    ) -> None:
        """Test deleting a conversation without x-user-id header."""
        # Arrange

        # Act
        response = client.delete("/api/v1/conversations/conv-123", headers={})

        # Assert
        assert response.status_code == 422  # Validation error
