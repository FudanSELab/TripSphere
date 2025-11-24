from typing import Annotated, Any, AsyncGenerator

from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.response import ServerSentEvent
from litestar.types import SSEData
from pydantic import BaseModel, Field

from chat.assistant.agent import ChatAssistantFacade
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
from chat.conversation.entities import Conversation, Message
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

    async def _find_validate_conversation(
        self,
        conversation_repository: ConversationRepository,
        conversation_id: str,
        user_id: str,
    ) -> Conversation:
        conversation = await conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(conversation_id)
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedException(conversation_id, user_id)
        return conversation

    async def _find_validate_task(
        self, task_repository: TaskRepository, task_id: str, conversation: Conversation
    ) -> Task:
        task = await task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        if task.conversation_id != conversation.conversation_id:
            raise Exception  # TODO: Define a proper exception
        if task.is_terminal_state():
            raise TaskImmutabilityException(task_id)
        return task

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
        conversation = await self._find_validate_conversation(
            conversation_repository, data.conversation_id, user_id
        )

        task_resume: Task | None = None
        if data.task_id is not None:
            task_resume = await self._find_validate_task(
                task_repository, data.task_id, conversation
            )

        user_query = await conversation_manager.add_text_query(
            conversation=conversation,
            query=data.content,
            associated_task=task_resume,
            metadata=data.metadata,
        )
        chat_assistant = ChatAssistantFacade(
            model_name="gpt-4o-mini",
            conversation_manager=conversation_manager,
            message_repository=message_repository,
            task_repository=task_repository,
        )
        state = await chat_assistant.invoke(conversation, user_query, task_resume)
        return ResponseBody(
            data=ChatResponse(
                query_id=user_query.message_id,
                answer_id=state.agent_answer.message_id,
                task_id=state.task.task_id if state.task else None,
            )
        )

    async def _stream_generator(
        self,
        conversation: Conversation,
        message: Message,
        task: Task | None,
        chat_assistant: ChatAssistantFacade,
    ) -> AsyncGenerator[SSEData, None]:
        async for chunk in chat_assistant.stream(conversation, message, task):
            yield chunk  # TODO: Wrap chunk into proper SSEData

    @post(":stream")
    async def stream_chat(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        conversation_manager: ConversationManager,
        task_repository: TaskRepository,
        data: ChatRequest,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> ServerSentEvent:
        conversation = await self._find_validate_conversation(
            conversation_repository, data.conversation_id, user_id
        )

        task_resume: Task | None = None
        if data.task_id is not None:
            task_resume = await self._find_validate_task(
                task_repository, data.task_id, conversation
            )

        user_query = await conversation_manager.add_text_query(
            conversation=conversation,
            query=data.content,
            associated_task=task_resume,
            metadata=data.metadata,
        )
        chat_assistant = ChatAssistantFacade(
            model_name="gpt-4o-mini",
            conversation_manager=conversation_manager,
            message_repository=message_repository,
            task_repository=task_repository,
        )

        return ServerSentEvent(
            self._stream_generator(
                conversation, user_query, task_resume, chat_assistant
            )
        )
