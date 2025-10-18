from abc import ABC, abstractmethod


class ConversationManager(ABC):
    @abstractmethod
    async def create_conversation(self, user_id: str) -> None: ...

    @abstractmethod
    async def append_message(self) -> None: ...
