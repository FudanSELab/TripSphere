from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient

from chat.config.settings import settings
from chat.infrastructure.mongodb.repositories import (
    MongoConversationRepository,
)
from chat.infrastructure.mongodb.schema import (
    ConversationItemDocument,
)
from chat.models import MessageRole, MessageSnapshot, Part
from chat.utils.base64 import encode_page_token
from chat.utils.uuid import uuid7


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncMongoClient[dict[str, Any]], None]:
    settings.mongodb.database = "test_database"
    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        "mongodb://localhost:27017", uuidRepresentation="standard"
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def conversation_repository(
    client: AsyncMongoClient[dict[str, Any]],
) -> AsyncGenerator[MongoConversationRepository, None]:
    repository = MongoConversationRepository(client)
    yield repository
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation"].delete_many({})
    await database["conversation_item"].delete_many({})


@pytest.mark.asyncio
async def test_list_conversation_items_backward(
    client: AsyncMongoClient[dict[str, Any]],
    conversation_repository: MongoConversationRepository,
) -> None:
    # Insert test data
    conversation_id = str(uuid7())
    documents = [
        ConversationItemDocument(
            _id=str(uuid7()),
            conversation_id=conversation_id,
            created_at=datetime.now(),
            content=MessageSnapshot(
                message_id=str(uuid7()),
                context_id=conversation_id,
                role=MessageRole.USER if i % 2 == 0 else MessageRole.AGENT,
                parts=[Part.model_validate({"text": f"Message {i}"})],
                extensions=None,
                reference_task_ids=None,
                metadata=None,
            ),
        ).model_dump()
        for i in range(20)
    ]
    database = client[settings.mongodb.database]
    async_collection = database["conversation_item"]
    insert_result = await async_collection.insert_many(documents)

    (
        items,
        next_page_token,
    ) = await conversation_repository.list_conversation_items(
        conversation_id=conversation_id,
        page_size=5,
        page_token=None,
        direction="backward",
    )
    assert len(items) == 5
    assert next_page_token == encode_page_token(insert_result.inserted_ids[15])
    for i, item in enumerate(items):
        assert isinstance(item.content, MessageSnapshot)
        assert item.content.text_content() == f"Message {19 - i}"

    (
        items,
        next_page_token,
    ) = await conversation_repository.list_conversation_items(
        conversation_id=conversation_id,
        page_size=10,
        page_token=next_page_token,
        direction="backward",
    )
    assert len(items) == 10
    assert next_page_token == encode_page_token(insert_result.inserted_ids[5])
    for i, item in enumerate(items):
        assert isinstance(item.content, MessageSnapshot)
        assert item.content.text_content() == f"Message {14 - i}"
