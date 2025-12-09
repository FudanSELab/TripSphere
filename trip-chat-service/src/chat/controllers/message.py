from typing import Annotated, Any, AsyncGenerator, cast

from httpx import AsyncClient
from litestar import Controller, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.params import Parameter
from litestar.response import ServerSentEvent, ServerSentEventMessage
from litestar.types import SSEData
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient

from chat.agent.facade import AgentFacade
from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
)
from chat.common.exceptions import (
    ConversationAccessDeniedException,
    ConversationNotFoundException,
    MessageNotFoundException,
)
from chat.common.parts import Part
from chat.conversation.manager import ConversationManager
from chat.conversation.models import Conversation, Message
from chat.conversation.repositories import ConversationRepository, MessageRepository
from chat.infra.nacos.naming import NacosNaming
from chat.utils.pagination import CursorPagination


class SendMessageRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID.")
    content: list[Part] = Field(..., description="Content of the query Message.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the query Message."
    )


class SendMessageResponse(BaseModel): ...


class MessageController(Controller):
    path = "/messages"
    tags = ["Messages"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "message_repository": Provide(provide_message_repository),
        "conversation_manager": Provide(provide_conversation_manager),
    }

    async def _find_conversation(
        self, conversation_repository: ConversationRepository, conversation_id: str
    ) -> Conversation:
        conversation = await conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(conversation_id)
        return conversation

    def _check_conversation_access(
        self, conversation: Conversation, user_id: str, **kwargs: Any
    ) -> Conversation:
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedException(
                conversation.conversation_id, user_id, **kwargs
            )
        return conversation

    @post(":send")
    async def send_message(self) -> SendMessageResponse:
        return SendMessageResponse()

    async def _stream_events(
        self,
        message_repository: MessageRepository,
        agent_facade: AgentFacade,
        conversation: Conversation,
        query: Message,
    ) -> AsyncGenerator[SSEData, None]:
        async for event in agent_facade.stream(conversation, query):
            if isinstance(event, Message):
                await message_repository.save(event)
                message = event.model_dump_json()
                yield ServerSentEventMessage(data=message, comment="final message")
            else:
                yield ServerSentEventMessage(
                    data=event.model_dump_json(),
                    id=event.id,
                    comment="google-adk event",
                )

    @post(":stream")
    async def stream_message(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        conversation_manager: ConversationManager,
        data: SendMessageRequest,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
        state: State,  # For accessing NacosNaming and AsyncClient
    ) -> ServerSentEvent:
        conversation = await self._find_conversation(
            conversation_repository, data.conversation_id
        )
        self._check_conversation_access(conversation, user_id)

        user_query = await conversation_manager.add_user_query(
            conversation, data.content, metadata=data.metadata
        )

        nacos_naming = cast(NacosNaming, state.get("nacos_naming"))
        httpx_client = cast(AsyncClient, state.get("httpx_client"))
        mongo_client = cast(AsyncMongoClient[dict[str, Any]], state.get("mongo_client"))
        agent_facade = await AgentFacade.create_facade(
            httpx_client, nacos_naming, mongo_client
        )

        return ServerSentEvent(
            self._stream_events(
                message_repository, agent_facade, conversation, user_query
            )
        )

    @get("/{message_id:str}")
    async def get_message(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        message_id: Annotated[str, Parameter(description="Message ID.")],
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> Message:
        message = await message_repository.find_by_id(message_id)
        if message is None:
            raise MessageNotFoundException(message_id)
        conversation = await self._find_conversation(
            conversation_repository, message.conversation_id
        )
        self._check_conversation_access(conversation, user_id, message_id=message_id)
        return message

    @get()
    async def list_messages(
        self,
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
        conversation_id: str,
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded Message ID.")
        ] = None,
    ) -> CursorPagination[str, Message]:
        conversation = await self._find_conversation(
            conversation_repository, conversation_id
        )
        self._check_conversation_access(conversation, user_id, resource="messages")
        messages, next_cursor = await conversation_manager.list_messages(
            conversation, results_per_page, cursor=cursor
        )
        pagination = CursorPagination[str, Message](
            items=messages, results_per_page=results_per_page, cursor=next_cursor
        )
        return pagination
