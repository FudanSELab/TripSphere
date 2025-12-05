from typing import Annotated

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.response import ServerSentEvent

from chat.common.deps import (
    provide_conversation_repository,
    provide_task_repository,
)
from chat.common.exceptions import (
    ConversationNotFoundException,
    TaskAccessDeniedException,
    TaskImmutabilityException,
    TaskNotFoundException,
)
from chat.common.schema import ResponseBody
from chat.conversation.repositories import ConversationRepository
from chat.task.models import Task
from chat.task.repositories import TaskRepository


class TaskController(Controller):
    path = "/tasks"
    tags = ["Tasks"]
    dependencies = {
        "conversation_repository": Provide(provide_conversation_repository),
        "task_repository": Provide(provide_task_repository),
    }

    @get("/{task_id:str}")
    async def get_task(
        self, task_repository: TaskRepository, task_id: str
    ) -> ResponseBody[Task]:
        task = await task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return ResponseBody(data=task)

    @post("/{task_id:str}:cancel")
    async def cancel_task(
        self,
        task_repository: TaskRepository,
        conversation_repository: ConversationRepository,
        task_id: str,
        user_id: Annotated[str, Parameter(header="X-User-Id")],
    ) -> None:
        task = await task_repository.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        conversation = await conversation_repository.find_by_id(task.conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(task.conversation_id)
        if conversation.user_id != user_id:
            raise TaskAccessDeniedException(task_id, user_id)
        if task.is_terminal():
            raise TaskImmutabilityException(task_id)
        raise NotImplementedError

    @post("/{task_id:str}:subscribe")
    async def subscribe_task(self, task_id: str) -> ServerSentEvent:
        raise NotImplementedError

    @post("/{task_id:str}:notify")  # A2A push notification webhook
    async def notify_task_update(self, task_id: str) -> None:
        raise NotImplementedError
