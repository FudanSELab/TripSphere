from abc import ABC, abstractmethod
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from chat.task.entities import Task


class TaskRepository(ABC):
    @abstractmethod
    async def save(self, task: Task) -> None: ...


class MongoTaskRepository(TaskRepository):
    COLLECTION_NAME = "tasks"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def save(self, task: Task) -> None:
        document = task.model_dump(by_alias=True)
        await self.collection.replace_one(
            {"_id": document["_id"]}, document, upsert=True
        )
