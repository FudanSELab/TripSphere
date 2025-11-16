from typing import Annotated, TypeAlias

from litestar import Controller, get
from litestar.params import Parameter

from chat.common.schema import ResponseBody
from chat.conversation.entities import Message
from chat.utils.pagination import CursorPagination

MessagePagination: TypeAlias = CursorPagination[str, Message]


class MessageController(Controller):
    path = "/messages"
    tags = ["Messages"]

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
        conversation_id: Annotated[
            str, Parameter(description="UUID string of the conversation.")
        ],
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded UUID.")
        ] = None,
    ) -> ResponseBody[MessagePagination]:
        raise NotImplementedError
