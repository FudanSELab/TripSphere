from typing import Annotated

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from litestar.params import Parameter

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
)
from chat.common.exceptions import (
    ConversationNotFoundException,
    MessageAccessDeniedException,
    MessageNotFoundException,
)
from chat.common.schema import ResponseBody
from chat.conversation.manager import ConversationManager
from chat.conversation.models import Message
from chat.conversation.repositories import ConversationRepository, MessageRepository
from chat.utils.pagination import CursorPagination

MessagePagination = CursorPagination[str, Message]


class MessageController(Controller):
    path = "/messages"
    tags = ["Messages"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "message_repository": Provide(provide_message_repository),
        "conversation_manager": Provide(provide_conversation_manager),
    }

    @get("/{message_id:str}")
    async def get_message(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        message_id: Annotated[str, Parameter(description="ID of the Message.")],
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> ResponseBody[Message]:
        message = await message_repository.find_by_id(message_id)
        if message is None:
            raise MessageNotFoundException(message_id)
        conversation = await conversation_repository.find_by_id(message.conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(message.conversation_id)
        if conversation.user_id != user_id:
            raise MessageAccessDeniedException(message_id, user_id)
        return ResponseBody(data=message)

    @get()
    async def list_messages(
        self,
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
        conversation_id: str,
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded Message UUID.")
        ] = None,
    ) -> ResponseBody[MessagePagination]:
        conversation = await conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(conversation_id)
        if conversation.user_id != user_id:
            raise PermissionDeniedException(
                detail=f"User {user_id} is not authorized to access the "
                f"messages of conversation {conversation_id}.",
                extra={"conversation_id": conversation_id, "user_id": user_id},
            )
        messages, next_cursor = await conversation_manager.list_messages(
            conversation, results_per_page, cursor=cursor
        )
        return ResponseBody(
            data=MessagePagination(
                items=messages,
                results_per_page=results_per_page,
                cursor=next_cursor,
            )
        )
