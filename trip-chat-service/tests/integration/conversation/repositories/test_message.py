from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from chat.common.parts import Part, TextPart
from chat.conversation.entities import Author, Message
from chat.conversation.repositories import MongoMessageRepository
from chat.utils.pagination import encode_uuid_cursor
from chat.utils.uuid import uuid7


@pytest_asyncio.fixture
async def collection() -> AsyncGenerator[AsyncCollection[dict[str, Any]], None]:
    client = AsyncMongoClient[dict[str, Any]]("mongodb://localhost:27017")
    yield client.get_database("test_database").get_collection(
        MongoMessageRepository.COLLECTION_NAME
    )
    await client.close()


@pytest_asyncio.fixture
async def message_repository(
    collection: AsyncCollection[dict[str, Any]],
) -> AsyncGenerator[MongoMessageRepository, None]:
    repository = MongoMessageRepository(collection)
    yield repository
    # Clean up the collection after each test
    await collection.delete_many({})


@pytest.mark.asyncio
async def test_list_by_conversation(
    collection: AsyncCollection[dict[str, Any]],
    message_repository: MongoMessageRepository,
) -> None:
    # Insert test documents
    conversation_id = str(uuid7())
    messages = [
        Message(
            conversation_id=conversation_id,
            author=Author.user() if i % 2 == 0 else Author.agent(),
            content=[Part.from_text(f"Message content {i}")],
            created_at=datetime.now(),
            metadata=None,
        )
        for i in range(20)
    ]
    documents = [message.model_dump(by_alias=True) for message in messages]
    insert_result = await collection.insert_many(documents)

    messages, next_token = await message_repository.list_by_conversation(
        conversation_id=conversation_id,
        limit=10,
        token=None,
        direction="backward",
    )
    assert len(messages) == 10
    assert next_token == encode_uuid_cursor(insert_result.inserted_ids[10])
    for i, message in enumerate(messages):
        assert message.content
        assert isinstance(message.content[0].root, TextPart)
        assert message.content[0].root.text == f"Message content {19 - i}"

    messages, next_token = await message_repository.list_by_conversation(
        conversation_id=conversation_id,
        limit=10,
        token=next_token,
        direction="backward",
    )
    assert len(messages) == 10
    assert next_token == encode_uuid_cursor(insert_result.inserted_ids[0])
    for i, message in enumerate(messages):
        assert message.content
        assert isinstance(message.content[0].root, TextPart)
        assert message.content[0].root.text == f"Message content {9 - i}"

    messages, next_token = await message_repository.list_by_conversation(
        conversation_id=conversation_id,
        limit=10,
        token=next_token,
        direction="backward",
    )
    assert len(messages) == 0
    assert next_token is None
