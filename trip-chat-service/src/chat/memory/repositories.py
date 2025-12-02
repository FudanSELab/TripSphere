from abc import ABC, abstractmethod
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from chat.memory.entities import Memory


class MemoryRepository(ABC):
    @abstractmethod
    async def save(self, memory: Memory) -> None: ...

    @abstractmethod
    async def find_by_id(self, memory_id: str) -> Memory | None: ...


class MongoMemoryRepository(MemoryRepository):
    COLLECTION_NAME = "memories"

    def __init__(self, collection: AsyncCollection[dict[str, Any]]) -> None:
        self.collection = collection

    async def save(self, memory: Memory) -> None:
        document = memory.model_dump(by_alias=True)
        await self.collection.replace_one(
            {"_id": document["_id"]}, document, upsert=True
        )

    async def find_by_id(self, memory_id: str) -> Memory | None:
        document = await self.collection.find_one({"_id": memory_id})
        if document is not None:
            return Memory.model_validate(document)
        return None
