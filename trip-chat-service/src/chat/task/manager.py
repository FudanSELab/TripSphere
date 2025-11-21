from typing import Literal

from chat.conversation.entities import Conversation
from chat.task.entities import Task
from chat.task.repositories import TaskRepository


class TaskManager:
    def __init__(self, task_repository: TaskRepository) -> None:
        self.task_repository = task_repository

    async def create_task(
        self, conversation: Conversation, task_type: Literal["local", "remote"]
    ) -> Task:
        raise NotImplementedError

    async def cancel_task(self, task: Task) -> None:
        if task.is_terminal_state():
            raise Exception  # TODO: Use proper exception
