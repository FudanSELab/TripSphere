from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class ResponseCode(IntEnum):
    """
    Application-specific response codes.
    """

    SUCCESS = 0


T = TypeVar("T")


class ResponseBody(BaseModel, Generic[T]):
    code: ResponseCode = Field(
        default=ResponseCode.SUCCESS, description="Application-specific response code."
    )
    message: str = Field(
        default="", description="Message providing additional information."
    )
    data: T = Field(..., description="Payload containing the response data.")
