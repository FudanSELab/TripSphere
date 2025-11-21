import logging
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai.agent import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from chat.common.parts import Part, TextPart
from chat.config.settings import get_settings
from chat.conversation.entities import Author, Message
from chat.prompts.assistant import CLASSIFY_INTENT, SIMPLE_RESPONSE
from chat.task.entities import Task

logger = logging.getLogger(__name__)


class Classification(BaseModel):
    intent: Literal["simple_response", "hotel_advice", "attraction_advice"] = Field(
        ..., description="The classification of user's intent."
    )
    summary: str = Field(..., description="A brief summary of the user's intent.")
    keywords: list[str] = Field(
        default_factory=list, description="Keywords extracted from the query."
    )


class ChatAssistantState(BaseModel):
    query_content: str
    classification: Classification | None = Field(default=None)
    author: Author = Field(default_factory=lambda: Author.agent())
    response: list[Part] = Field(default_factory=list[Part])
    task: Task | None = Field(default=None)


@dataclass
class SimpleResponse(BaseNode[ChatAssistantState, None, None]):
    chat_model: OpenAIChatModel

    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        simple_agent = Agent(
            self.chat_model, output_type=str, instructions=SIMPLE_RESPONSE
        )
        result = await simple_agent.run(ctx.state.query_content)
        ctx.state.author = Author.agent("chat-assistant")
        ctx.state.response.append(Part.from_text(result.output))
        return End(None)


@dataclass
class HotelAdvice(BaseNode[ChatAssistantState, None, None]):
    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        return End(None)  # TODO: Invoke remote agent through A2A


@dataclass
class AttractionAdvice(BaseNode[ChatAssistantState, None, None]):
    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        return End(None)  # TODO: Invoke remote agent through A2A


@dataclass
class ClassifyIntent(BaseNode[ChatAssistantState]):
    chat_model: OpenAIChatModel

    async def run(
        self, ctx: GraphRunContext[ChatAssistantState]
    ) -> SimpleResponse | HotelAdvice | AttractionAdvice:
        classify_agent = Agent(
            self.chat_model, output_type=Classification, instructions=CLASSIFY_INTENT
        )
        result = await classify_agent.run(ctx.state.query_content)
        logger.debug(result.all_messages())
        ctx.state.classification = result.output
        match result.output.intent:
            case "simple_response":
                return SimpleResponse(chat_model=self.chat_model)
            case "hotel_advice":
                return HotelAdvice()
            case "attraction_advice":
                return AttractionAdvice()
            case _:
                raise ValueError(f"Unknown intent: {result.output.intent}")


@dataclass
class Initialize(BaseNode[ChatAssistantState]):
    chat_model: OpenAIChatModel

    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> ClassifyIntent:
        return ClassifyIntent(chat_model=self.chat_model)


class ChatAssistant:
    def __init__(self, model_name: str = "gpt-4o") -> None:
        self.model_name = model_name
        self.graph = Graph[ChatAssistantState](
            nodes=[
                Initialize,
                ClassifyIntent,
                SimpleResponse,
                HotelAdvice,
                AttractionAdvice,
            ]
        )

    async def run(self, message: Message) -> ChatAssistantState:
        settings = get_settings()
        base_url = settings.openai.base_url
        api_key = settings.openai.api_key.get_secret_value()
        chat_model = OpenAIChatModel(
            self.model_name,
            provider=OpenAIProvider(base_url=base_url, api_key=api_key),
            settings=ModelSettings(temperature=0),
        )
        init_node = Initialize(chat_model=chat_model)
        # Currently, we only use the text parts of the message
        text_parts = [
            part.root.text
            for part in message.content
            if isinstance(part.root, TextPart)
        ]
        state = ChatAssistantState(query_content="\n".join(text_parts))
        await self.graph.run(init_node, state=state)
        return state
