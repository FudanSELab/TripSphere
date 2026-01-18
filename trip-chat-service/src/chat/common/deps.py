from typing import Annotated, Any, cast

from fastapi import Depends, Request
from httpx import AsyncClient
from pymongo import AsyncMongoClient

from chat.config.settings import get_settings
from chat.infra.nacos.ai import NacosAI
from chat.internal.manager import ConversationManager
from chat.internal.repository import (
    ConversationRepository,
    MessageRepository,
    MongoConversationRepository,
    MongoMessageRepository,
)


def provide_httpx_client(request: Request) -> AsyncClient:
    return cast(AsyncClient, request.app.state.httpx_client)


def provide_mongo_client(request: Request) -> AsyncMongoClient[dict[str, Any]]:
    return cast(AsyncMongoClient[dict[str, Any]], request.app.state.mongo_client)


def provide_nacos_ai(request: Request) -> NacosAI:
    return cast(NacosAI, request.app.state.nacos_ai)


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
