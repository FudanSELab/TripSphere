from typing import Any, cast

from litestar.datastructures import State
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import (
    ConversationRepository,
    MessageRepository,
    MongoConversationRepository,
    MongoMessageRepository,
)
from chat.task.manager import TaskManager
from chat.task.repositories import MongoTaskRepository, TaskRepository


async def provide_conversation_repository(state: State) -> ConversationRepository:
    mongo_client = cast(AsyncMongoClient[dict[str, Any]], state.mongo_client)
    settings = get_settings()
    database = mongo_client.get_database(settings.mongo.database)
    return MongoConversationRepository(
        database.get_collection(MongoConversationRepository.COLLECTION_NAME)
    )


async def provide_message_repository(state: State) -> MessageRepository:
    mongo_client = cast(AsyncMongoClient[dict[str, Any]], state.mongo_client)
    settings = get_settings()
    database = mongo_client.get_database(settings.mongo.database)
    return MongoMessageRepository(
        database.get_collection(MongoMessageRepository.COLLECTION_NAME)
    )


async def provide_conversation_manager(
    conversation_repository: ConversationRepository,
    message_repository: MessageRepository,
) -> ConversationManager:
    return ConversationManager(conversation_repository, message_repository)


async def provide_task_repository(state: State) -> TaskRepository:
    mongo_client = cast(AsyncMongoClient[dict[str, Any]], state.mongo_client)
    settings = get_settings()
    database = mongo_client.get_database(settings.mongo.database)
    return MongoTaskRepository(
        database.get_collection(MongoTaskRepository.COLLECTION_NAME)
    )


async def provide_task_manager(task_repository: TaskRepository) -> TaskManager:
    return TaskManager(task_repository)
