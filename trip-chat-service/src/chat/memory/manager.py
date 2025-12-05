from chat.conversation.models import Conversation, Message
from chat.memory.models import Memory


class MemoryManager:
    def __init__(self) -> None: ...

    def extract(self, messages: list[Message]) -> list[Memory]:
        raise NotImplementedError

    def search(self, conversation: Conversation) -> list[Memory]:
        raise NotImplementedError
