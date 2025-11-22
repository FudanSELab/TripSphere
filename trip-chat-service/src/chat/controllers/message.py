from typing import Annotated, TypeAlias

from litestar import Controller, get
from litestar.di import Provide
from litestar.params import Parameter

from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
)
from chat.common.exceptions import ConversationNotFoundException
from chat.common.schema import ResponseBody
from chat.conversation.entities import Message
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import ConversationRepository
from chat.utils.pagination import CursorPagination

MessagePagination: TypeAlias = CursorPagination[str, Message]


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
        message_id: Annotated[
            str, Parameter(description="UUID string of the message.")
        ],
    ) -> ResponseBody[Message]:
        raise NotImplementedError

    @get()
    async def list_messages(
        self,
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager,
        conversation_id: Annotated[
            str, Parameter(description="UUID string of the conversation.")
        ],
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded message UUID.")
        ] = None,
    ) -> ResponseBody[MessagePagination]:
        conversation = await conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(conversation_id)
        messages, next_cursor = await conversation_manager.list_messages(
            conversation, results_per_page, cursor
        )
        return ResponseBody(
            data=MessagePagination(
                items=messages,
                results_per_page=results_per_page,
                cursor=next_cursor,
            )
        )
