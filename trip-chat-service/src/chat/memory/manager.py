from chat.conversation.entities import Conversation, Message
from chat.memory.entities import Memory


class MemoryManager:
    def __init__(self) -> None: ...

    def extract(self, messages: list[Message]) -> list[Memory]:
        raise NotImplementedError

    def search(self, conversation: Conversation) -> list[Memory]:
        raise NotImplementedError
