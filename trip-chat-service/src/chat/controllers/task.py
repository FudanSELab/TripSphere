from litestar import Controller, get, post
from litestar.di import Provide

from chat.common.deps import provide_task_manager, provide_task_repository
from chat.task.manager import TaskManager
from chat.task.repositories import TaskRepository


class TaskController(Controller):
    path = "/tasks"
    tags = ["Tasks"]
    dependencies = {
        "task_repository": Provide(provide_task_repository),
        "task_manager": Provide(provide_task_manager),
    }

    @get("/{task_id:str}")
    async def get_task(self, task_id: str) -> None: ...

    @post("/{task_id:str}:notify")
    async def notify_task_update(self, task_id: str) -> None: ...

    @post("/{task_id:str}:cancel")
    async def cancel_task(
        self, task_repository: TaskRepository, task_manager: TaskManager, task_id: str
    ) -> None:
        task = await task_repository.find_by_id(task_id)
        if task is None:
            raise Exception  # TODO: Use proper exception
        await task_manager.cancel_task(task)

    @post("/{task_id:str}:subscribe")
    async def subscribe_task(self, task_id: str) -> None: ...
