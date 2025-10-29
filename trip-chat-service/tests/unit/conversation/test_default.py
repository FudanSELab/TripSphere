from datetime import datetime

import pytest
import pytest_mock
from a2a.types import Message, Part, Role, TextPart
from bson import ObjectId

from chat.conversation.default import DefaultConversationManager
from chat.exceptions import ConversationNotFoundError
from chat.persistence.mongodb.schema import ConversationDocument, MessageDocument
from chat.utils.base64 import encode_page_token
from chat.utils.uuid import uuid7


@pytest.mark.asyncio
async def test_create_conversation_success(mocker: pytest_mock.MockerFixture) -> None:
    conversation_id = ObjectId()
    user_id = str(uuid7())
    metadata = {"key": "value"}

    conversation_collection = mocker.Mock()
    conversation_item_collection = mocker.Mock()
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )

    conversation_collection.insert = mocker.AsyncMock(
        return_value=ConversationDocument(
            _id=str(conversation_id),
            user_id=user_id,
            created_at=datetime.now(),
            metadata=metadata,
        )
    )

    conversation = await conversation_manager.create_conversation(
        user_id=user_id, metadata=metadata
    )

    assert conversation.conversation_id == str(conversation_id)
    assert conversation.user_id == user_id
    assert conversation.metadata == metadata
    conversation_collection.insert.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_conversation_success(mocker: pytest_mock.MockerFixture) -> None:
    conversation_collection = mocker.Mock()
    conversation_item_collection = mocker.Mock()
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )

    document = ConversationDocument(
        _id=str(ObjectId()),
        user_id=str(uuid7()),
        created_at=datetime.now(),
        metadata={"key": "value"},
    )
    conversation_collection.find_by_id = mocker.AsyncMock(return_value=document)

    assert document.id is not None
    conversation = await conversation_manager.get_conversation(document.id)

    assert conversation.conversation_id == document.id
    assert conversation.user_id == document.user_id
    assert conversation.metadata == document.metadata
    assert conversation.created_at == document.created_at
    conversation_collection.find_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_conversation_not_found(mocker: pytest_mock.MockerFixture) -> None:
    conversation_collection = mocker.Mock()
    conversation_item_collection = mocker.Mock()
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )

    conversation_collection.find_by_id = mocker.AsyncMock(return_value=None)

    conversation_id = str(ObjectId())
    with pytest.raises(ConversationNotFoundError) as exc_info:
        await conversation_manager.get_conversation(conversation_id)

    assert "not found" in str(exc_info.value).lower()
    assert exc_info.value.conversation_id == conversation_id
    conversation_collection.find_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_conversation_items_desc(mocker: pytest_mock.MockerFixture) -> None:
    # Prepare test data
    conversation_id = ObjectId()
    messages = [
        MessageDocument(
            _id=uuid7(),
            conversation_id=str(conversation_id),
            role=Role.user if i % 2 == 0 else Role.agent,
            created_at=datetime.now(),
            parts=[Part(root=TextPart(text=f"Message {i}"))],
        )
        for i in range(20)
    ]

    conversation_collection = mocker.Mock()
    conversation_item_collection = mocker.Mock()
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )

    conversation_collection.find_by_id = mocker.AsyncMock(
        return_value=ConversationDocument(
            _id=str(conversation_id),
            user_id=str(uuid7()),
            created_at=datetime.now(),
            metadata={"key": "value"},
        )
    )

    conversation_item_collection.list_by_conversation = mocker.AsyncMock(
        return_value=(
            list(reversed(messages[15:20])),
            20,
            encode_page_token(messages[15].id),
        )
    )

    result = await conversation_manager.list_conversation_items(
        str(conversation_id), page_size=5, page_token=None, order="desc"
    )
    items = result["items"]
    total_count = result["total_count"]
    next_page_token = result["next_page_token"]

    assert len(items) == 5 and total_count == 20
    conversation_item_collection.list_by_conversation.assert_awaited_once()
    assert next_page_token == encode_page_token(messages[15].id)
    for i, item in enumerate(items):
        assert isinstance(item.content, Message)
        assert isinstance(item.content.parts[0].root, TextPart)
        assert item.content.parts[0].root.text == f"Message {19 - i}"

    conversation_item_collection.list_by_conversation = mocker.AsyncMock(
        return_value=(
            list(reversed(messages[5:15])),
            20,
            encode_page_token(messages[5].id),
        )
    )

    result = await conversation_manager.list_conversation_items(
        str(conversation_id), page_size=10, page_token=next_page_token, order="desc"
    )
    items = result["items"]
    total_count = result["total_count"]
    next_page_token = result["next_page_token"]

    assert len(items) == 10 and total_count == 20
    conversation_item_collection.list_by_conversation.assert_awaited_once()
    assert next_page_token == encode_page_token(messages[5].id)
    for i, item in enumerate(items):
        assert isinstance(item.content, Message)
        assert isinstance(item.content.parts[0].root, TextPart)
        assert item.content.parts[0].root.text == f"Message {14 - i}"
