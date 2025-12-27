from typing import Self

from pydantic import BaseModel, Field
from rocketmq.v5.model import (  # type: ignore
    Message as RocketmqMessage,
)  # pyright: ignore[reportMissingTypeStubs]


class Message(BaseModel):
    """A typed RocketMQ message representation."""

    message_id: str = Field(...)
    body: bytes | None = Field(default=None)
    tag: str | None = Field(default=None)

    @classmethod
    def from_rmq_message(cls, message: RocketmqMessage) -> Self:
        """Create a typed Message from a RocketMQ Message."""
        raise NotImplementedError
