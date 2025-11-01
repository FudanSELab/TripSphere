from datetime import datetime

import pytest
import pytest_mock

from chat.conversation.default import DefaultConversationManager
from chat.exceptions import ConversationNotFoundError
from chat.models import Conversation
from chat.utils.uuid import uuid7


@pytest.mark.asyncio
async def test_create_conversation_success(mocker: pytest_mock.MockerFixture) -> None:
    user_id = str(uuid7())
    metadata = {"key": "value"}

    conversation_repository = mocker.Mock()
    conversation_manager = DefaultConversationManager(conversation_repository)

    conversation_repository.save = mocker.AsyncMock(
        return_value=Conversation(user_id=user_id, metadata=metadata)
    )

    conversation = await conversation_manager.create_conversation(
        user_id=user_id, metadata=metadata
    )

    assert conversation.user_id == user_id
    assert conversation.metadata == metadata
    conversation_repository.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_conversation_success(mocker: pytest_mock.MockerFixture) -> None:
    conversation_id = str(uuid7())
    user_id = str(uuid7())
    metadata = {"key": "value"}
    created_at = datetime.now()

    conversation_repository = mocker.Mock()
    conversation_manager = DefaultConversationManager(conversation_repository)

    conversation_repository.find_by_id = mocker.AsyncMock(
        return_value=Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata,
            created_at=created_at,
        )
    )

    conversation = await conversation_manager.get_conversation(conversation_id)

    assert conversation.conversation_id == conversation_id
    assert conversation.user_id == user_id
    assert conversation.metadata == metadata
    assert conversation.created_at == created_at
    conversation_repository.find_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_conversation_not_found(mocker: pytest_mock.MockerFixture) -> None:
    conversation_repository = mocker.Mock()
    conversation_manager = DefaultConversationManager(conversation_repository)

    conversation_repository.find_by_id = mocker.AsyncMock(return_value=None)

    conversation_id = "non_existent_id"
    with pytest.raises(ConversationNotFoundError) as exc_info:
        await conversation_manager.get_conversation(conversation_id)

    assert "not found" in str(exc_info.value).lower()
    assert exc_info.value.conversation_id == conversation_id
    conversation_repository.find_by_id.assert_awaited_once()
