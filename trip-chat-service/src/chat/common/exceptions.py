from typing import Any

from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
)


class MessageNotFoundException(NotFoundException):
    def __init__(self, message_id: str):
        """
        Raised when a Message is not found.
        """
        super().__init__(
            f"Message {message_id} is not found.", extra={"message_id": message_id}
        )


class MessageImmutabilityException(HTTPException):
    def __init__(self, message_id: str):
        """
        Once a Message reaches a terminal state, it cannot be modified.
        """
        super().__init__(
            detail=f"Message {message_id} has reached a terminal state,"
            " and it cannot be modified.",
            status_code=409,  # 409: Conflict with the current state of Message
            extra={"message_id": message_id},
        )


class ConversationNotFoundException(NotFoundException):
    def __init__(self, conversation_id: str):
        """
        Raised when a Conversation is not found.
        """
        super().__init__(
            f"Conversation {conversation_id} is not found.",
            extra={"conversation_id": conversation_id},
        )


class ConversationAccessDeniedException(PermissionDeniedException):
    def __init__(self, conversation_id: str, user_id: str, **kwargs: Any):
        """
        Raised when a user tries to access a Conversation that doesn't belong to them.
        """
        # Pop conversation_id and user_id to prevent duplication
        kwargs.pop("conversation_id", None)
        kwargs.pop("user_id", None)
        super().__init__(
            f"User {user_id} is not authorized to access "
            f"conversation {conversation_id}.",
            extra={"conversation_id": conversation_id, "user_id": user_id, **kwargs},
        )
