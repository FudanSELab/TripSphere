class ConversationNotFoundError(Exception):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(f"Conversation with ID {conversation_id} is not found.")
        self.conversation_id = conversation_id
