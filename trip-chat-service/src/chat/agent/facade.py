import logging
from typing import Any, AsyncGenerator

from pydantic import BaseModel, Field

from chat.conversation.entities import Conversation, Message
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import MessageRepository
from chat.task.entities import Task
from chat.task.repositories import TaskRepository

logger = logging.getLogger(__name__)


class IntentAnalysis(BaseModel):
    summary: str = Field(..., description="A brief summary of user's intent.")
    keywords: list[str] = Field(
        default_factory=list, description="Keywords associated with the intent."
    )


class AgentFacade:
    def __init__(
        self,
        model_name: str,
        conversation_manager: ConversationManager,
        message_repository: MessageRepository,
        task_repository: TaskRepository,
    ) -> None:
        self.model_name = model_name
        # Dependency injections
        self.conversation_manager = conversation_manager
        self.message_repository = message_repository
        self.task_repository = task_repository

    async def _analyze_intent(self) -> IntentAnalysis: ...

    async def invoke(
        self,
        conversation: Conversation,
        message: Message,
        associated_task: Task | None = None,
    ) -> Any: ...

    async def stream(
        self,
        conversation: Conversation,
        message: Message,
        associated_task: Task | None = None,
    ) -> AsyncGenerator[Any, None]:  # TODO: Specify proper type
        yield
