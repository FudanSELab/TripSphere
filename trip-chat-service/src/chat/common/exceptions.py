from typing import Any

from fastapi.exceptions import HTTPException


class NotFoundException(HTTPException, ValueError):
    """Cannot find the requested resource."""

    def __init__(self, message: str = "", extra: dict[str, Any] | None = None):
        super().__init__(
            status_code=404,  # 404: Not Found
            detail={"message": message, "extra": extra},
        )


class PermissionDeniedException(HTTPException):
    """Request understood, but not authorized."""

    def __init__(self, message: str = "", extra: dict[str, Any] | None = None):
        super().__init__(
            status_code=403,  # 403: Forbidden
            detail={"message": message, "extra": extra},
        )


class MessageNotFoundException(NotFoundException):
    """Raised when a Message is not found."""

    def __init__(self, message_id: str):
        super().__init__(
            f"Message {message_id} is not found.", extra={"message_id": message_id}
        )


class ConversationNotFoundException(NotFoundException):
    """Raised when a Conversation is not found."""

    def __init__(self, conversation_id: str):
        super().__init__(
            f"Conversation {conversation_id} is not found.",
            extra={"conversation_id": conversation_id},
        )


class ConversationAccessDeniedException(PermissionDeniedException):
    """Raised when user tries to access Conversation that doesn't belong to them."""

    def __init__(self, conversation_id: str, user_id: str, **kwargs: Any):
        # Pop conversation_id and user_id to prevent duplication
        kwargs.pop("conversation_id", None)
        kwargs.pop("user_id", None)
        super().__init__(
            f"User {user_id} is not authorized to access "
            f"conversation {conversation_id}.",
            extra={"conversation_id": conversation_id, "user_id": user_id, **kwargs},
        )
