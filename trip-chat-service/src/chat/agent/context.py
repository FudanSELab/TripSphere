from chat.conversation.models import Message
from chat.memory.models import Memory


class ContextProvider:
    def __init__(self) -> None: ...

    async def memories(self) -> list[Memory]:
        return []

    async def history_messages(self) -> list[Message]:
        return []
