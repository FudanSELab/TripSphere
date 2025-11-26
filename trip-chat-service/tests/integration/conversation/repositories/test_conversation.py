from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from chat.conversation.entities import Conversation
from chat.conversation.repositories import MongoConversationRepository
from chat.utils.pagination import encode_uuid_cursor
from chat.utils.uuid import uuid7


@pytest_asyncio.fixture
async def collection() -> AsyncGenerator[AsyncCollection[dict[str, Any]], None]:
    client = AsyncMongoClient[dict[str, Any]]("mongodb://localhost:27017")
    yield client.get_database("test_database").get_collection(
        MongoConversationRepository.COLLECTION_NAME
    )
    await client.close()


@pytest_asyncio.fixture
async def conversation_repository(
    collection: AsyncCollection[dict[str, Any]],
) -> AsyncGenerator[MongoConversationRepository, None]:
    repository = MongoConversationRepository(collection)
    yield repository
    # Clean up the collection after each test
    await collection.delete_many({})


@pytest.mark.asyncio
async def test_list_by_user(
    collection: AsyncCollection[dict[str, Any]],
    conversation_repository: MongoConversationRepository,
) -> None:
    # Insert test documents
    user_id = str(uuid7())
    conversations = [
        Conversation(
            user_id=user_id,
            title=f"Conversation {i}",
            created_at=datetime.now(),
            metadata={"index": i},
        )
        for i in range(20)
    ]
    documents = [conv.model_dump(by_alias=True) for conv in conversations]
    insert_result = await collection.insert_many(documents)

    conversations, next_token = await conversation_repository.list_by_user(
        user_id=user_id,
        limit=10,
        token=None,
        direction="backward",
    )
    assert len(conversations) == 10
    assert next_token == encode_uuid_cursor(insert_result.inserted_ids[10])
    for i, conversation in enumerate(conversations):
        assert conversation.title == f"Conversation {19 - i}"
        assert conversation.metadata == {"index": 19 - i}

    # Fetch the next page
    conversations, next_token = await conversation_repository.list_by_user(
        user_id=user_id,
        limit=10,
        token=next_token,
        direction="backward",
    )
    assert len(conversations) == 10
    assert next_token == encode_uuid_cursor(insert_result.inserted_ids[0])
    for i, conversation in enumerate(conversations):
        assert conversation.title == f"Conversation {9 - i}"
        assert conversation.metadata == {"index": 9 - i}

    # Fetch beyond the last page
    conversations, next_token = await conversation_repository.list_by_user(
        user_id=user_id,
        limit=10,
        token=next_token,
        direction="backward",
    )
    assert len(conversations) == 0
    assert next_token is None
