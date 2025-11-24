from typing import Annotated, Any, TypeAlias

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.params import Parameter
from pydantic import BaseModel, Field

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
    provide_task_repository,
)
from chat.common.exceptions import (
    ConversationAccessDeniedException,
    ConversationNotFoundException,
)
from chat.common.schema import ResponseBody
from chat.conversation.entities import Conversation
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import ConversationRepository
from chat.utils.pagination import CursorPagination

ConversationPagination: TypeAlias = CursorPagination[str, Conversation]


class CreateConversationRequest(BaseModel):
    title: str | None = Field(
        default=None, description="Optional specified conversation title."
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the conversation."
    )


class ConversationController(Controller):
    path = "/conversations"
    tags = ["Conversations"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "message_repository": Provide(provide_message_repository),
        "conversation_manager": Provide(provide_conversation_manager),
    }

    @post()
    async def create_conversation(
        self,
        conversation_manager: ConversationManager,
        data: CreateConversationRequest,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> ResponseBody[Conversation]:
        conversation = await conversation_manager.create_conversation(
            user_id=user_id, title=data.title, metadata=data.metadata
        )
        return ResponseBody(data=conversation)

    @get()
    async def list_user_conversations(
        self,
        conversation_repository: ConversationRepository,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded UUID.")
        ] = None,
    ) -> ResponseBody[ConversationPagination]:
        conversations, next_cursor = await conversation_repository.list_by_user(
            user_id, limit=results_per_page, token=cursor, direction="backward"
        )
        pagination = ConversationPagination(
            items=conversations,
            results_per_page=results_per_page,
            cursor=next_cursor,
        )
        return ResponseBody(data=pagination)

    @delete(
        "/{conversation_id:str}",
        dependencies={
            "task_repository": Provide(provide_task_repository),
        },
    )
    async def delete_conversation(
        self,
        conversation_repository: ConversationRepository,
        conversation_id: str,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> None:
        conversation = await conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedException(conversation_id, user_id)
        raise NotImplementedError
