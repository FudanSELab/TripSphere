from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
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
    def __init__(self, conversation_id: str, user_id: str):
        """
        Raised when a user tries to access a not owned conversation.
        """
        super().__init__(
            f"User {user_id} is not authorized to access "
            f"conversation {conversation_id}.",
            extra={"conversation_id": conversation_id, "user_id": user_id},
        )


class TaskNotFoundException(NotFoundException):
    def __init__(self, task_id: str):
        """
        Raised when a Task is not found.
        """
        super().__init__(f"Task {task_id} is not found.", extra={"task_id": task_id})


class TaskAccessDeniedException(PermissionDeniedException):
    def __init__(self, conversation_id: str, task_id: str, user_id: str):
        """
        Raised when a user tries to access a not owned task.
        """
        super().__init__(
            f"User {user_id} is not authorized to access "
            f"task {task_id} in conversation {conversation_id}.",
            extra={
                "conversation_id": conversation_id,
                "task_id": task_id,
                "user_id": user_id,
            },
        )


class TaskImmutabilityException(HTTPException):
    def __init__(self, task_id: str):
        """
        Once a task reaches a terminal state
        (completed, cancelled, rejected, or failed), it cannot be modified.
        """
        super().__init__(
            detail=f"Task {task_id} has reached a terminal state "
            "and it cannot be restarted or modified.",
            status_code=409,
            extra={"task_id": task_id},
        )
