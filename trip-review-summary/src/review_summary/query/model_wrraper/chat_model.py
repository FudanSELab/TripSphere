from typing import Any, AsyncGenerator, Dict, List

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    convert_to_messages,
)
from langchain_openai import ChatOpenAI


class ModelWrapper:
    def __init__(self, model: ChatOpenAI, **kwargs: Any):
        self.chat_model = model

    def _build_messages(
        self, query: str, history: List[dict[str, str]] | None = None
    ) -> List[BaseMessage]:
        messages: list[BaseMessage] = []
        if history:
            messages.extend(convert_to_messages(history))
        messages.append(HumanMessage(content=query))
        return messages

    def chat_non_stream(
        self, query: str, history: List[Dict[str, str]] | None = None
    ) -> str:
        """
        Non-streaming call: returns the complete response as a string.

        Args:
            query: User input.
            history: Conversation history
            (a list where each element is a dict of the form
            {"role": "user" or "assistant", "content": "message"}).

        Returns:
            The complete model response as a string.
        """
        messages = self._build_messages(query, history)
        response = self.chat_model.invoke(messages)
        return response.content

    async def chat_stream(
        self, query: str, history: List[Dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Streaming call: returns an async generator that yields
        response chunks incrementally.

        Args:
            query: User input.
            history: Conversation history (a list where each element is
            a dict of the form
            {"role": "user" or "assistant", "content": "message"}).

        Returns:
            AsyncGenerator[str, None]: An asynchronous generator
            yielding response chunks as strings.
        """
        messages = self._build_messages(query, history)

        async for chunk in self.chat_model.astream(messages):
            if chunk.content:
                yield chunk.content
