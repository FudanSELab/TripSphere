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
