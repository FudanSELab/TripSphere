from chat.common.exceptions import TaskImmutabilityException
from chat.task.entities import Task
from chat.task.repositories import TaskRepository


class TaskManager:
    def __init__(self, task_repository: TaskRepository) -> None:
        self.task_repository = task_repository

    async def create_from_a2a(self) -> Task:
        raise NotImplementedError

    async def cancel_task(self, task: Task) -> None:
        if task.is_terminal_state():
            raise TaskImmutabilityException(task.task_id)
        raise NotImplementedError
