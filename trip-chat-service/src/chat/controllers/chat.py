from typing import Annotated, Any

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Parameter
from pydantic import BaseModel, Field

from chat.assistant.agent import ChatAssistant
from chat.common.deps import (
    provide_conversation_manager,
    provide_conversation_repository,
    provide_message_repository,
    provide_task_repository,
)
from chat.common.exceptions import (
    ConversationAccessDeniedException,
    ConversationNotFoundException,
    TaskImmutabilityException,
    TaskNotFoundException,
)
from chat.common.schema import ResponseBody
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import ConversationRepository, MessageRepository
from chat.task.entities import Task
from chat.task.repositories import TaskRepository


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="UUID of the conversation.")
    task_id: str | None = Field(
        default=None, description="Optional UUID of an existing task to resume."
    )
    content: str = Field(..., description="User sent chat message content.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the query message."
    )


class ChatResponse(BaseModel):
    query_id: str = Field(..., description="UUID of the user query message.")
    answer_id: str = Field(..., description="UUID of the agent answer message.")
    task_id: str | None = Field(
        default=None, description="Optional UUID of the associated task."
    )


class ChatController(Controller):
    path = "/chat"
    tags = ["Chat"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "message_repository": Provide(provide_message_repository),
        "conversation_manager": Provide(provide_conversation_manager),
        "task_repository": Provide(provide_task_repository),
    }

    @post()
    async def chat(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        conversation_manager: ConversationManager,
        task_repository: TaskRepository,
        data: ChatRequest,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> ResponseBody[ChatResponse]:
        conversation = await conversation_repository.find_by_id(data.conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(data.conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedException(data.conversation_id, user_id)

        task_resume: Task | None = None
        if data.task_id is not None:
            task_resume = await task_repository.find_by_id(data.task_id)
            if task_resume is None:
                raise TaskNotFoundException(data.task_id)
            if task_resume.conversation_id != conversation.conversation_id:
                raise Exception  # TODO: Define a proper exception
            if task_resume.is_terminal_state():
                raise TaskImmutabilityException(data.task_id)

        user_query = await conversation_manager.add_text_query(
            conversation=conversation,
            query=data.content,
            associated_task=task_resume,
            metadata=data.metadata,
        )
        chat_assistant = ChatAssistant(
            model_name="gpt-4o-mini",
            conversation_manager=conversation_manager,
            message_repository=message_repository,
            task_repository=task_repository,
        )
        state = await chat_assistant.invoke(
            conversation=conversation, message=user_query, associated_task=task_resume
        )
        return ResponseBody(
            data=ChatResponse(
                query_id=user_query.message_id,
                answer_id=state.agent_answer.message_id,
                task_id=state.task.task_id if state.task else None,
            )
        )
