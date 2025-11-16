from litestar import Controller, post


class TaskController(Controller):
    path = "/tasks"
    tags = ["Tasks"]

    @post("/{task_id:str}:notify")
    async def notify_task_update(self, task_id: str) -> None:
        """ """
        ...

    @post("/{task_id:str}:cancel")
    async def cancel_task(self, task_id: str) -> None: ...

    @post("/{task_id:str}:subscribe")
    async def subscribe_task(self, task_id: str) -> None: ...
