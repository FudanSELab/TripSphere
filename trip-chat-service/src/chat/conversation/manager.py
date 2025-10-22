from abc import ABC, abstractmethod
from typing import Any


class ConversationManager(ABC):
    @abstractmethod
    async def create_conversation(
        self, user_id: str, metadata: dict[str, Any] | None = None
    ) -> None: ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> None: ...
