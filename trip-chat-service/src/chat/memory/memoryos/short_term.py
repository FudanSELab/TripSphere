import logging

from chat.memory.memoryos.core import DialogPage

logger = logging.getLogger(__name__)


class ShortTermMemory:
    def __init__(self, max_capacity: int) -> None:
        self.max_capacity = max_capacity

    async def push_page(self, page: DialogPage) -> None: ...
