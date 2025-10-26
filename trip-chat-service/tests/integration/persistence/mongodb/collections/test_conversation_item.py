from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from a2a.types import Part, Role, TextPart
from bson import ObjectId
from pymongo import AsyncMongoClient

from chat.config.settings import settings
from chat.persistence.mongodb.collections import ConversationItemCollection
from chat.persistence.mongodb.schema import MessageDocument
from chat.utils.base64 import encode_page_token


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncMongoClient[dict[str, Any]], None]:
    settings.mongodb.database = "test_database"
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        "mongodb://localhost:27017"
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def collection(
    client: AsyncMongoClient[dict[str, Any]],
) -> AsyncGenerator[ConversationItemCollection, None]:
    collection = ConversationItemCollection(client)
    yield collection
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation_item"].delete_many({})


@pytest.mark.asyncio
async def test_list_by_conversation_desc(
    client: AsyncMongoClient[dict[str, Any]], collection: ConversationItemCollection
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

    result = await collection.list_by_conversation(
        conversation_id=str(conversation_id),
        page_size=5,
        page_token=None,
        order="desc",
    )
    items, total, next_page_token = result
    assert len(items) == 5
    assert total == 20
    assert next_page_token == encode_page_token(insert_result.inserted_ids[15])
    for i, item in enumerate(items):
        assert isinstance(item, MessageDocument)
        assert isinstance(item.parts[0].root, TextPart)
        assert item.parts[0].root.text == f"Message {19 - i}"

    result = await collection.list_by_conversation(
        conversation_id=str(conversation_id),
        page_size=10,
        page_token=next_page_token,
        order="desc",
    )
    items, total, next_page_token = result
    assert len(items) == 10
    assert total == 20
    assert next_page_token == encode_page_token(insert_result.inserted_ids[5])
    for i, item in enumerate(items):
        assert isinstance(item, MessageDocument)
        assert isinstance(item.parts[0].root, TextPart)
        assert item.parts[0].root.text == f"Message {14 - i}"
