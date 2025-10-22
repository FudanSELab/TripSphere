from abc import ABC, abstractmethod
from typing import Generic, TypeVar

MemoryContent = TypeVar("MemoryContent")
RetrievalResult = TypeVar("RetrievalResult")


class MemoryManager(ABC, Generic[MemoryContent, RetrievalResult]):
    @abstractmethod
    async def add(self, conversation_id: str, content: MemoryContent) -> None: ...

    @abstractmethod
    async def retrieve(self, conversation_id: str, query: str) -> RetrievalResult: ...
