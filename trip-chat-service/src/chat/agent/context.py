from pydantic_ai.messages import ModelMessage


class ContextProvider:
    def __init__(self) -> None: ...

    async def history_messages(self) -> list[ModelMessage]:
        return []
