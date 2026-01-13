from typing import Self

from pydantic import BaseModel, Field
from rocketmq.v5.model import Message as RocketmqMessage  # type: ignore


class Message(BaseModel):
    """A typed RocketMQ Message representation."""

    message_id: str = Field(...)
    body: bytes | None = Field(default=None)
    tag: str | None = Field(default=None)

    @classmethod
    def from_rmq_message(cls, message: RocketmqMessage) -> Self:
        """Create a typed Message from a RocketMQ Message."""
        return cls(
            message_id=getattr(message, "message_id"),  # noqa: B009
            body=getattr(message, "body", None),
            tag=getattr(message, "tag", None),
        )


class CreateReview(BaseModel):
    id: str = Field(..., alias="ID", description="Unique identifier for the review.")
    text: str = Field(..., alias="Text", description="Content of the review.")
    target_id: str = Field(
        ...,
        alias="TargetID",
        description="Unique identifier for the target object of the review.",
    )
