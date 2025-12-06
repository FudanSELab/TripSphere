import json
from base64 import b64decode
from datetime import datetime
from mimetypes import guess_type

from pydantic_ai import ModelMessage, ModelRequest, ModelResponse
from pydantic_ai.messages import (
    AudioUrl,
    BinaryContent,
    DocumentUrl,
    ImageUrl,
    ModelRequestPart,
    ModelResponsePart,
    UserPromptPart,
    VideoUrl,
)
from pydantic_ai.messages import FilePart as AIFilePart
from pydantic_ai.messages import TextPart as AITextPart

from chat.common.parts import DataPart, Part, TextPart
from chat.conversation.models import Conversation, Message
from chat.conversation.repositories import MessageRepository
from chat.memory.models import Memory


class ContextProvider:
    def __init__(
        self, conversation: Conversation, message_repository: MessageRepository
    ) -> None:
        self.conversation = conversation
        self.message_repository = message_repository

    async def memories(self) -> list[Memory]:
        return []

    async def history_messages(self, exclude_last: bool) -> list[Message]:
        messages, _ = await self.message_repository.list_by_conversation(
            self.conversation.conversation_id, limit=20, direction="backward"
        )
        messages.reverse()  # From the oldest to the newest
        if exclude_last is True and len(messages) > 0:
            messages = messages[:-1]
        return messages


def convert_message(message: Message) -> ModelMessage:
    timestamp = message.created_at
    if message.author.role == "user":
        return ModelRequest(
            parts=[convert_request_part(part, timestamp) for part in message.content],
            metadata=message.metadata,
        )
    elif message.author.role == "agent":
        return ModelResponse(
            parts=[convert_response_part(part, timestamp) for part in message.content],
            metadata=message.metadata,
        )
    else:
        raise ValueError(f"Unknown Message Author Role: {message.author.role}")


def convert_request_part(part: Part, timestamp: datetime) -> ModelRequestPart:
    if isinstance(part.root, TextPart):
        return UserPromptPart(content=part.root.text, timestamp=timestamp)

    if isinstance(part.root, DataPart):
        data = json.dumps(part.root.data)
        return UserPromptPart(content=data, timestamp=timestamp)

    file = part.root
    media_type: str | None = None
    if file.mime_type is not None:
        media_type = file.mime_type
    elif file.name is not None:
        media_type, _ = guess_type(file.name)
    media_type = media_type or "application/octet-stream"

    if file.bytes is not None:
        return UserPromptPart(
            content=[
                BinaryContent(
                    data=b64decode(file.bytes),
                    media_type=media_type,
                    identifier=file.name,
                )
            ],
            timestamp=timestamp,
        )

    if media_type.startswith("image/"):
        return UserPromptPart(
            [ImageUrl(str(file.uri), media_type=media_type, identifier=file.name)],
            timestamp=timestamp,
        )
    elif media_type.startswith("video/"):
        return UserPromptPart(
            [VideoUrl(str(file.uri), media_type=media_type, identifier=file.name)],
            timestamp=timestamp,
        )
    elif media_type.startswith("audio/"):
        return UserPromptPart(
            [AudioUrl(str(file.uri), media_type=media_type, identifier=file.name)],
            timestamp=timestamp,
        )
    else:
        return UserPromptPart(
            [DocumentUrl(str(file.uri), media_type=media_type, identifier=file.name)],
            timestamp=timestamp,
        )


def convert_response_part(part: Part, timestamp: datetime) -> ModelResponsePart:
    if isinstance(part.root, TextPart):
        return AITextPart(content=part.root.text)

    if isinstance(part.root, DataPart):
        return AITextPart(content=json.dumps(part.root.data))

    file = part.root
    if file.uri is not None:
        return AITextPart(content=json.dumps(file))

    media_type: str | None = None
    if file.mime_type is not None:
        media_type = file.mime_type
    elif file.name is not None:
        media_type, _ = guess_type(file.name)
    return AIFilePart(
        content=BinaryContent(
            data=b64decode(str(file.bytes)),
            media_type=media_type or "application/octet-stream",
            identifier=file.name,
        )
    )
