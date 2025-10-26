from datetime import datetime

from a2a.types import Message, Task
from pydantic import BaseModel

from chat.memory.manager import MemoryManager
from chat.memory.memoryos.mid_term import MidTermMemory
from chat.memory.memoryos.short_term import ShortTermMemory


class DialogPage(BaseModel):
    query: Message
    response: Message | Task
    timestamp: datetime


class QueryResult(BaseModel): ...


class MemoryosMemoryManager(MemoryManager[DialogPage, QueryResult]):
    def __init__(self, short_term_capacity: int) -> None:
        self.short_term_memory = ShortTermMemory(short_term_capacity)
        self.mid_term_memory = MidTermMemory()

    async def add(self, conversation_id: str, content: DialogPage) -> None: ...

    async def retrieve(self, conversation_id: str, query: str) -> QueryResult:
        return QueryResult()
