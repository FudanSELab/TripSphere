from typing import Annotated, Any, AsyncGenerator

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from httpx import AsyncClient
from mem0 import AsyncMemory  # type: ignore
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient

from chat.agent.facade import AgentFacade
from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_httpx_client,
    provide_memory_engine,
    provide_message_repository,
    provide_mongo_client,
    provide_nacos_ai,
)
from chat.common.exceptions import (
    ConversationAccessDeniedException,
    ConversationNotFoundException,
    MessageNotFoundException,
)
from chat.common.parts import Part
from chat.infra.nacos.ai import NacosAI
from chat.internal.manager import ConversationManager
from chat.internal.models import Conversation, Message
from chat.internal.repository import ConversationRepository, MessageRepository
from chat.utils.pagination import CursorPagination
from chat.utils.sse import encode


class SendMessageRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID.")
    content: list[Part] = Field(..., description="Content of the query Message.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the query Message."
    )


class SendMessageResponse(BaseModel):
    query_id: str = Field(..., description="ID of the sent query Message.")
    agent_answer: Message = Field(..., description="Agent's answer Message.")
    metadata: dict[str, Any] | None = Field(default=None)


messages = APIRouter(prefix="/messages", tags=["Messages"])


async def _find_conversation(
    conversation_repository: ConversationRepository, conversation_id: str
) -> Conversation:
    conversation = await conversation_repository.find_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFoundException(conversation_id)
    return conversation


def _check_conversation_access(
    conversation: Conversation, user_id: str, **kwargs: Any
) -> Conversation:
    if conversation.user_id != user_id:
        raise ConversationAccessDeniedException(
            conversation.conversation_id, user_id, **kwargs
        )
    return conversation


@messages.post("/send")
async def send_message(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    message_repository: Annotated[
        MessageRepository, Depends(provide_message_repository)
    ],
    conversation_manager: Annotated[
        ConversationManager, Depends(provide_conversation_manager)
    ],
    request: SendMessageRequest,
    x_user_id: Annotated[str, Header()],
    httpx_client: Annotated[AsyncClient, Depends(provide_httpx_client)],
    mongo_client: Annotated[
        AsyncMongoClient[dict[str, Any]], Depends(provide_mongo_client)
    ],
    nacos_ai: Annotated[NacosAI, Depends(provide_nacos_ai)],
    memory_engine: Annotated[AsyncMemory, Depends(provide_memory_engine)],
) -> SendMessageResponse:
    conversation = await _find_conversation(
        conversation_repository, request.conversation_id
    )
    _check_conversation_access(conversation, x_user_id)

    user_query = await conversation_manager.add_user_query(
        conversation, request.content, metadata=request.metadata
    )
    agent_facade = await AgentFacade.create_facade(
        httpx_client, nacos_ai, mongo_client, memory_engine
    )
    agent_answer = await agent_facade.invoke(conversation, user_query)
    await message_repository.save(agent_answer)
    return SendMessageResponse(
        query_id=user_query.message_id, agent_answer=agent_answer
    )


async def _stream_events(
    message_repository: MessageRepository,
    agent_facade: AgentFacade,
    conversation: Conversation,
    query: Message,
) -> AsyncGenerator[str, None]:
    async for event in agent_facade.stream(conversation, query):
        data = event.model_dump_json()
        if isinstance(event, Message):
            await message_repository.save(event)
            event_id = event.message_id
            # Yield the final message to be rendered
            yield encode(data=data, event_id=event_id, comment="final message")
        else:
            # Yield intermediate Google ADK events
            yield encode(data=data, event_id=event.id, comment="google-adk event")


@messages.post("/stream")
async def stream_message(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    message_repository: Annotated[
        MessageRepository, Depends(provide_message_repository)
    ],
    conversation_manager: Annotated[
        ConversationManager, Depends(provide_conversation_manager)
    ],
    request: SendMessageRequest,
    x_user_id: Annotated[str, Header()],
    httpx_client: Annotated[AsyncClient, Depends(provide_httpx_client)],
    mongo_client: Annotated[
        AsyncMongoClient[dict[str, Any]], Depends(provide_mongo_client)
    ],
    nacos_ai: Annotated[NacosAI, Depends(provide_nacos_ai)],
    memory_engine: Annotated[AsyncMemory, Depends(provide_memory_engine)],
) -> StreamingResponse:
    conversation = await _find_conversation(
        conversation_repository, request.conversation_id
    )
    _check_conversation_access(conversation, x_user_id)

    user_query = await conversation_manager.add_user_query(
        conversation, request.content, metadata=request.metadata
    )
    agent_facade = await AgentFacade.create_facade(
        httpx_client, nacos_ai, mongo_client, memory_engine
    )
    return StreamingResponse(
        _stream_events(message_repository, agent_facade, conversation, user_query),
        media_type="text/event-stream",
    )


@messages.get("/{message_id}", response_model_by_alias=False)
async def get_message(
    message_repository: Annotated[
        MessageRepository, Depends(provide_message_repository)
    ],
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    x_user_id: Annotated[str, Header()],
    message_id: str,
) -> Message:
    message = await message_repository.find_by_id(message_id)
    if message is None:
        raise MessageNotFoundException(message_id)
    conversation = await _find_conversation(
        conversation_repository, message.conversation_id
    )
    _check_conversation_access(conversation, x_user_id, message_id=message_id)
    return message


@messages.get("", response_model_by_alias=False)
async def list_conversation_messages(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    conversation_manager: Annotated[
        ConversationManager, Depends(provide_conversation_manager)
    ],
    x_user_id: Annotated[str, Header()],
    conversation_id: str,
    results_per_page: int,
    cursor: str | None = None,
) -> CursorPagination[str, Message]:
    conversation = await _find_conversation(conversation_repository, conversation_id)
    _check_conversation_access(conversation, x_user_id, resource="messages")
    pagination = await conversation_manager.list_conversation_messages(
        conversation, results_per_page, direction="backward", cursor=cursor
    )
    return pagination
