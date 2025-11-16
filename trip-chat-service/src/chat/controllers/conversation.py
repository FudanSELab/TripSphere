from typing import Annotated, TypeAlias

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.params import Parameter

from chat.common.deps import provide_conversation_repository
from chat.common.schema import ResponseBody
from chat.conversation.entities import Conversation
from chat.conversation.repositories import ConversationRepository
from chat.utils.pagination import CursorPagination

ConversationPagination: TypeAlias = CursorPagination[str, Conversation]


class ConversationController(Controller):
    path = "/conversations"
    tags = ["Conversations"]

    @post(
        dependencies={
            "conversation_repository": Provide(provide_conversation_repository)
        }
    )
    async def create_conversation(
        self,
        conversation_repository: ConversationRepository,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> ResponseBody[Conversation]:
        raise NotImplementedError

    @get()
    async def list_conversations(
        self,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
        results_per_page: int,
        cursor: Annotated[
            str | None, Parameter(description="Base64-encoded UUID.")
        ] = None,
    ) -> ResponseBody[ConversationPagination]:
        raise NotImplementedError

    @delete("/{conversation_id:str}")
    async def delete_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError
