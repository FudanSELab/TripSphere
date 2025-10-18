from datetime import datetime

from pydantic import BaseModel, Field

from chat.memory.manager import MemoryManager
from chat.memory.memoryos.mid_term import MidTermMemory
from chat.memory.memoryos.short_term import ShortTermMemory


class DialogPage(BaseModel):
    query: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.now)


class QueryResult(BaseModel): ...


class Memoryos(MemoryManager[DialogPage, QueryResult]):
    def __init__(self, short_term_capacity: int) -> None:
        self.short_term_memory = ShortTermMemory(short_term_capacity)
        self.mid_term_memory = MidTermMemory()

    async def add(self, session_id: str, content: DialogPage) -> None: ...

    async def retrieve(self, session_id: str, query: str) -> QueryResult:
        return QueryResult()
