import logging
from typing import Any, cast

from google.adk.memory.base_memory_service import (
    BaseMemoryService,
    SearchMemoryResponse,
)
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.sessions.session import Session
from google.genai import types
from mem0 import AsyncMemory  # type: ignore

logger = logging.getLogger(__name__)


class Mem0MemoryService(BaseMemoryService):
    def __init__(self, memory_engine: AsyncMemory) -> None:
        self.memory_engine = memory_engine

    async def add_session_to_memory(self, session: Session) -> None:
        user_id = session.user_id
        messages: list[dict[str, Any]] = []
        for event in session.events:
            if not event.content or not event.content.parts:
                continue
            role = "user" if event.author == "user" else "assistant"
            messages.append(
                {
                    "role": role,
                    "content": event.content.model_dump(mode="json", exclude_none=True),
                }
            )
        if len(messages) > 0:
            result = await self.memory_engine.add(messages=messages, user_id=user_id)  # pyright: ignore
            logger.info("Added session to memory")
            logger.debug(f"Memory engine add response: {result}")
        else:
            logger.info("No messages to add to memory.")

    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> SearchMemoryResponse:
        search_result = await self.memory_engine.search(query=query, user_id=user_id)  # pyright: ignore
        search_result = cast(dict[str, list[dict[str, Any]] | None], search_result)
        retrieved_results = search_result.get("results", [])
        if not retrieved_results:
            return SearchMemoryResponse(memories=[])
        memory_entries: list[MemoryEntry] = []
        for retrieved_result in retrieved_results:
            metadata: dict[str, Any] = retrieved_result.pop("metadata", None) or {}
            memory_entry = MemoryEntry(
                id=retrieved_result.pop("id"),
                content=types.Content(
                    parts=[types.Part(text=retrieved_result.pop("memory"))]
                ),
                timestamp=retrieved_result.pop("created_at"),
                custom_metadata={**retrieved_result, **metadata},
            )
            memory_entries.append(memory_entry)
        return SearchMemoryResponse(memories=memory_entries)
