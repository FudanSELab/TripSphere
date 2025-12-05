from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")
C = TypeVar("C", int, str, UUID)


class CursorPagination(BaseModel, Generic[C, T]):
    """
    Container for data returned using cursor pagination.
    """

    items: list[T] = Field(
        ..., description="List of data being sent as part of the response."
    )
    results_per_page: int = Field(..., description="Maximal number of items to send.")
    cursor: C | None = Field(
        None, description="Designating the last identifier in the given items."
    )


UUIDStr = str


def encode_uuid_cursor(uid: UUIDStr | None) -> str | None:
    """
    Arguments:
        uid: UUID string to encode.

    Returns:
        Base64-encoded UUID string or None if `uid` is None.
    """
    if uid is None:
        return None
    return urlsafe_b64encode(UUID(uid).bytes).decode("utf-8")


def decode_uuid_cursor(cursor: str | None) -> UUIDStr | None:
    """
    Arguments:
        cursor: Base64-encoded UUID string to decode.

    Returns:
        Decoded UUID string or None if `cursor` is None.
    """
    if cursor is None:
        return None
    binary = urlsafe_b64decode(cursor.encode("utf-8"))
    return str(UUID(bytes=binary))
