from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
)
from chat.common.exceptions import (
    ConversationAccessDeniedException,
    ConversationNotFoundException,
)
from chat.internal.manager import ConversationManager
from chat.internal.models import Conversation
from chat.internal.repository import ConversationRepository
from chat.utils.pagination import CursorPagination


class CreateConversationRequest(BaseModel):
    title: str | None = Field(
        default=None, description="Optional specified conversation title."
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the conversation."
    )


conversations = APIRouter(prefix="/conversations", tags=["Conversations"])


@conversations.post("", status_code=201, response_model_by_alias=False)
async def create_conversation(
    conversation_manager: Annotated[
        ConversationManager, Depends(provide_conversation_manager)
    ],
    request: CreateConversationRequest,
    x_user_id: Annotated[str, Header()],
) -> Conversation:
    conversation = await conversation_manager.create_conversation(
        user_id=x_user_id, title=request.title, metadata=request.metadata
    )
    return conversation


@conversations.get("", response_model_by_alias=False)
async def list_user_conversations(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    x_user_id: Annotated[str, Header()],
    results_per_page: int,
    cursor: str | None = None,
) -> CursorPagination[str, Conversation]:
    pagination = await conversation_repository.list_by_user(
        x_user_id, limit=results_per_page, direction="backward", token=cursor
    )
    return pagination


@conversations.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_repository: Annotated[
        ConversationRepository, Depends(provide_conversation_repository)
    ],
    conversation_manager: Annotated[
        ConversationManager, Depends(provide_conversation_manager)
    ],
    conversation_id: str,
    x_user_id: Annotated[str, Header()],
) -> None:
    conversation = await conversation_repository.find_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFoundException(conversation_id)
    if conversation.user_id != x_user_id:
        raise ConversationAccessDeniedException(conversation_id, x_user_id)
    await conversation_manager.delete_conversation(conversation)
