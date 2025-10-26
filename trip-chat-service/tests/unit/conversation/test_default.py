from datetime import datetime
from typing import Any, AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from a2a.types import Message, Part, Role, TextPart
from bson import ObjectId
from pymongo import AsyncMongoClient

from chat.config.settings import settings
from chat.conversation.default import DefaultConversationManager
from chat.persistence.mongodb.collections import (
    ConversationCollection,
    ConversationItemCollection,
)
from chat.persistence.mongodb.schema import MessageDocument


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncMongoClient[dict[str, Any]], None]:
    settings.mongodb.database = "test_database"
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        "mongodb://localhost:27017"
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def conversation_collection(
    client: AsyncMongoClient[dict[str, Any]],
) -> AsyncGenerator[ConversationCollection, None]:
    collection = ConversationCollection(client)
    yield collection
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation"].delete_many({})


@pytest_asyncio.fixture
async def conversation_item_collection(
    client: AsyncMongoClient[dict[str, Any]],
) -> AsyncGenerator[ConversationItemCollection, None]:
    collection = ConversationItemCollection(client)
    yield collection
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation_item"].delete_many({})


@pytest.mark.asyncio
async def test_create_conversation(
    conversation_collection: ConversationCollection,
    conversation_item_collection: ConversationItemCollection,
) -> None:
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )
    user_id = str(uuid4())
    conversation = await conversation_manager.create_conversation(
        user_id=user_id, metadata={"key": "value"}
    )
    assert conversation.conversation_id is not None
    assert conversation.user_id == user_id
    assert conversation.metadata == {"key": "value"}


@pytest.mark.asyncio
async def test_update_conversation(
    conversation_collection: ConversationCollection,
    conversation_item_collection: ConversationItemCollection,
) -> None:
    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )
    user_id = str(uuid4())
    conversation = await conversation_manager.create_conversation(
        user_id=user_id, metadata={"key": "value"}
    )
    assert conversation.conversation_id is not None
    updated_conversation = await conversation_manager.update_conversation(
        conversation_id=conversation.conversation_id,
        metadata={"new_key": "new_value"},
    )
    assert updated_conversation.conversation_id == conversation.conversation_id
    assert updated_conversation.user_id == user_id
    assert updated_conversation.metadata == {"new_key": "new_value"}


@pytest.mark.asyncio
async def test_list_conversation_items_desc(
    client: AsyncMongoClient[dict[str, Any]],
    conversation_collection: ConversationCollection,
    conversation_item_collection: ConversationItemCollection,
) -> None:
    # Insert test data
    conversation_id = ObjectId()
    messages = [
        MessageDocument(
            conversation_id=str(conversation_id),
            role=Role.user if i % 2 == 0 else Role.agent,
            created_at=datetime.now(),
            parts=[Part(root=TextPart(text=f"Message {i}"))],
        ).model_dump(by_alias=True, exclude_none=True)
        for i in range(20)
    ]
    database = client[settings.mongodb.database]
    async_collection = database["conversation_item"]
    insert_result = await async_collection.insert_many(messages)

    conversation_manager = DefaultConversationManager(
        conversation_collection, conversation_item_collection
    )

    result = await conversation_manager.list_conversation_items(
        conversation_id=str(conversation_id),
        page_size=5,
        page_token=None,
        order="desc",
    )
    items, total, next_page_token = result
    assert len(items) == 5
    assert total == 20
    assert next_page_token == conversation_item_collection.encode_token(
        insert_result.inserted_ids[15]
    )
    for i, item in enumerate(items):
        assert isinstance(item.content, Message)
        assert isinstance(item.content.parts[0].root, TextPart)
        assert item.content.parts[0].root.text == f"Message {19 - i}"

    result = await conversation_manager.list_conversation_items(
        conversation_id=str(conversation_id),
        page_size=10,
        page_token=next_page_token,
        order="desc",
    )
    items, total, next_page_token = result
    assert len(items) == 10
    assert total == 20
    assert next_page_token == conversation_item_collection.encode_token(
        insert_result.inserted_ids[5]
    )
    for i, item in enumerate(items):
        assert isinstance(item.content, Message)
        assert isinstance(item.content.parts[0].root, TextPart)
        assert item.content.parts[0].root.text == f"Message {14 - i}"
