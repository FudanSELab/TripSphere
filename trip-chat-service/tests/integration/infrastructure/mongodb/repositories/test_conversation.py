from datetime import datetime
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient

from chat.config.settings import settings
from chat.infrastructure.mongodb.repositories import (
    ConversationItemRepository,
    ConversationRepository,
)
from chat.infrastructure.mongodb.schema import (
    ConversationDocument,
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
) -> AsyncGenerator[ConversationRepository, None]:
    repository = ConversationRepository(client)
    yield repository
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation"].delete_many({})


@pytest_asyncio.fixture
async def conversation_item_repository(
    client: AsyncMongoClient[dict[str, Any]],
) -> AsyncGenerator[ConversationItemRepository, None]:
    repository = ConversationItemRepository(client)
    yield repository
    # Clean up the collection after each test
    database = client[settings.mongodb.database]
    await database["conversation_item"].delete_many({})


@pytest.mark.asyncio
async def test_conversation_save_and_find_by_id(
    conversation_repository: ConversationRepository,
) -> None:
    conversation = ConversationDocument(
        _id=str(uuid7()),
        user_id=str(uuid7()),
        created_at=datetime.now(),
        metadata={"topic": "Test Conversation"},
    ).to_model()

    await conversation_repository.save(conversation)
    fetched_conversation = await conversation_repository.find_by_id(
        conversation.conversation_id
    )

    assert fetched_conversation is not None
    assert fetched_conversation.conversation_id == conversation.conversation_id
    assert fetched_conversation.user_id == conversation.user_id
    assert fetched_conversation.metadata == conversation.metadata


@pytest.mark.asyncio
async def test_conversation_find_by_id_not_found(
    conversation_repository: ConversationRepository,
) -> None:
    fetched_conversation = await conversation_repository.find_by_id("non_existent_id")
    assert fetched_conversation is None


@pytest.mark.asyncio
async def test_conversation_remove_by_id(
    client: AsyncMongoClient[dict[str, Any]],
    conversation_repository: ConversationRepository,
) -> None:
    # Insert test data
    conversation_id = str(uuid7())
    document = ConversationDocument(
        _id=conversation_id,
        user_id=str(uuid7()),
        created_at=datetime.now(),
        metadata={"topic": "Test Conversation"},
    ).model_dump()
    database = client[settings.mongodb.database]
    async_collection = database["conversation"]
    await async_collection.insert_one(document)

    deleted_count = await conversation_repository.remove_by_id(conversation_id)
    assert deleted_count == 1

    count = await async_collection.count_documents({"_id": conversation_id})
    assert count == 0


@pytest.mark.asyncio
async def test_conversation_item_save_and_find_by_id(
    conversation_item_repository: ConversationItemRepository,
) -> None:
    conversation_item = ConversationItemDocument(
        _id=str(uuid7()),
        conversation_id=str(uuid7()),
        created_at=datetime.now(),
        content=MessageSnapshot(
            message_id=str(uuid7()),
            context_id=str(uuid7()),
            role=MessageRole.USER,
            parts=[Part.model_validate({"text": "Hello, world!"})],
            extensions=None,
            reference_task_ids=None,
            metadata=None,
        ),
    ).to_model()

    await conversation_item_repository.save(conversation_item)
    fetched_item = await conversation_item_repository.find_by_id(
        conversation_item.item_id
    )

    assert fetched_item is not None
    assert fetched_item.item_id == conversation_item.item_id
    assert isinstance(fetched_item.content, MessageSnapshot)
    assert fetched_item.content.text_content() == "Hello, world!"


@pytest.mark.asyncio
async def test_conversation_item_find_by_id_not_found(
    conversation_item_repository: ConversationItemRepository,
) -> None:
    fetched_item = await conversation_item_repository.find_by_id("non_existent_id")
    assert fetched_item is None


@pytest.mark.asyncio
async def test_conversation_item_remove_by_conversation_id(
    client: AsyncMongoClient[dict[str, Any]],
    conversation_item_repository: ConversationItemRepository,
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
    await async_collection.insert_many(documents)

    await conversation_item_repository.remove_by_conversation_id(conversation_id)

    count = await async_collection.count_documents({"conversation_id": conversation_id})
    assert count == 0


@pytest.mark.asyncio
async def test_conversation_item_find_all_by_conversation_id_desc(
    client: AsyncMongoClient[dict[str, Any]],
    conversation_item_repository: ConversationItemRepository,
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
        total,
        next_page_token,
    ) = await conversation_item_repository.find_all_by_conversation_id(
        conversation_id=conversation_id,
        page_size=5,
        page_token=None,
        order="desc",
    )
    assert len(items) == 5
    assert total == 20
    assert next_page_token == encode_page_token(insert_result.inserted_ids[15])
    for i, item in enumerate(items):
        assert isinstance(item.content, MessageSnapshot)
        assert item.content.text_content() == f"Message {19 - i}"

    (
        items,
        total,
        next_page_token,
    ) = await conversation_item_repository.find_all_by_conversation_id(
        conversation_id=conversation_id,
        page_size=10,
        page_token=next_page_token,
        order="desc",
    )
    assert len(items) == 10
    assert total == 20
    assert next_page_token == encode_page_token(insert_result.inserted_ids[5])
    for i, item in enumerate(items):
        assert isinstance(item.content, MessageSnapshot)
        assert item.content.text_content() == f"Message {14 - i}"
