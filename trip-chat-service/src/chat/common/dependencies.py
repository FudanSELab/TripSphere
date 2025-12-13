from typing import Annotated, Any, cast

from fastapi import Depends, Request
from httpx import AsyncClient
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import (
    ConversationRepository,
    MessageRepository,
    MongoConversationRepository,
    MongoMessageRepository,
)
from chat.infra.nacos.naming import NacosNaming


def provide_httpx_client(request: Request) -> AsyncClient:
    return cast(AsyncClient, request.app.state.httpx_client)


def provide_mongo_client(request: Request) -> AsyncMongoClient[dict[str, Any]]:
    return cast(AsyncMongoClient[dict[str, Any]], request.app.state.mongo_client)


def provide_nacos_naming(request: Request) -> NacosNaming:
    return cast(NacosNaming, request.app.state.nacos_naming)


async def provide_conversation_repository(
    mongo_client: Annotated[
        AsyncMongoClient[dict[str, Any]], Depends(provide_mongo_client)
    ],
) -> ConversationRepository:
    settings = get_settings()
    database = mongo_client.get_database(settings.mongo.database)
    return MongoConversationRepository(
        database.get_collection(MongoConversationRepository.COLLECTION_NAME)
    )


async def provide_message_repository(
    mongo_client: Annotated[
        AsyncMongoClient[dict[str, Any]], Depends(provide_mongo_client)
    ],
) -> MessageRepository:
    settings = get_settings()
    database = mongo_client.get_database(settings.mongo.database)
    return MongoMessageRepository(
        database.get_collection(MongoMessageRepository.COLLECTION_NAME)
    )


async def provide_conversation_manager(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    message_repository: Annotated[
        MessageRepository, Depends(provide_message_repository)
    ],
) -> ConversationManager:
    return ConversationManager(conversation_repository, message_repository)
