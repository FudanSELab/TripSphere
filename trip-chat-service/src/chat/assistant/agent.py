import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, AsyncGenerator, Literal

from pydantic import BaseModel, Field
from pydantic_ai.agent import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from chat.common.parts import Part
from chat.config.settings import get_settings
from chat.conversation.entities import Conversation, Message
from chat.conversation.manager import ConversationManager
from chat.conversation.repositories import MessageRepository
from chat.prompts.assistant import CHAT_ASSISTANT, CLASSIFY_INTENT
from chat.task.entities import Task
from chat.task.repositories import TaskRepository

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
    conversation: Conversation
    user_query: Message
    classification: Classification | None = Field(default=None)
    agent_answer: Message
    task: Task | None = Field(default=None)


@dataclass
class SimpleResponse(BaseNode[ChatAssistantState, None, None]):
    chat_model: OpenAIChatModel

    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        naive_chat_agent = Agent(
            self.chat_model, output_type=str, instructions=CHAT_ASSISTANT
        )
        result = await naive_chat_agent.run(ctx.state.user_query.text_content())
        ctx.state.agent_answer.author.name = "chat-assistant"
        ctx.state.agent_answer.content.append(Part.from_text(result.output))
        return End(None)


@dataclass
class HotelAdvice(BaseNode[ChatAssistantState, None, None]):
    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        ctx.state.agent_answer.author.name = "hotel-advisor"
        return End(None)  # TODO: Invoke remote agent through A2A


@dataclass
class AttractionAdvice(BaseNode[ChatAssistantState, None, None]):
    async def run(self, ctx: GraphRunContext[ChatAssistantState]) -> End:
        ctx.state.agent_answer.author.name = "attraction-advisor"
        return End(None)  # TODO: Invoke remote agent through A2A


@dataclass
class ClassifyIntent(BaseNode[ChatAssistantState]):
    chat_model: OpenAIChatModel

    async def run(
        self, ctx: GraphRunContext[ChatAssistantState]
    ) -> SimpleResponse | HotelAdvice | AttractionAdvice:
        agent: str | None = None
        if ctx.state.user_query.metadata:
            agent = ctx.state.user_query.metadata.get("agent")
        if ctx.state.task is not None:
            agent = ctx.state.task.task_agent
        match agent:
            case "chat-assistant":
                return SimpleResponse(chat_model=self.chat_model)
            case "hotel-advisor":
                return HotelAdvice()
            case "attraction-advisor":
                return AttractionAdvice()
            case _:
                ...  # Fallback to agentic classification
        intent_classifier = Agent(
            model=self.chat_model,
            output_type=Classification,
            instructions=[CHAT_ASSISTANT, CLASSIFY_INTENT],
        )
        result = await intent_classifier.run(ctx.state.user_query.text_content())
        ctx.state.classification = result.output
        match ctx.state.classification.intent:
            case "simple_response":
                return SimpleResponse(chat_model=self.chat_model)
            case "hotel_advice":
                return HotelAdvice()
            case "attraction_advice":
                return AttractionAdvice()


@lru_cache(maxsize=1, typed=True)
def get_pydantic_graph() -> Graph[ChatAssistantState]:
    return Graph[ChatAssistantState](
        nodes=[ClassifyIntent, SimpleResponse, HotelAdvice, AttractionAdvice]
    )


class ChatAssistantFacade:
    def __init__(
        self,
        model_name: str,
        conversation_manager: ConversationManager,
        message_repository: MessageRepository,
        task_repository: TaskRepository,
    ) -> None:
        self.model_name = model_name
        self.conversation_manager = conversation_manager
        self.message_repository = message_repository
        self.task_repository = task_repository
        self.graph = get_pydantic_graph()

    async def invoke(
        self,
        conversation: Conversation,
        message: Message,
        associated_task: Task | None = None,
    ) -> ChatAssistantState:
        # Append a new empty agent answer message to the conversation
        agent_answer = await self.conversation_manager.add_empty_answer(
            conversation=conversation, associated_task=associated_task
        )

        openai = get_settings().openai
        chat_model = OpenAIChatModel(
            self.model_name,
            provider=OpenAIProvider(
                base_url=openai.base_url,
                api_key=openai.api_key.get_secret_value(),
            ),
            settings=ModelSettings(temperature=0),
        )
        start_node = ClassifyIntent(chat_model=chat_model)
        initial_state = ChatAssistantState(
            conversation=conversation,
            user_query=message,
            agent_answer=agent_answer,
            task=associated_task,
        )
        result = await self.graph.run(start_node, state=initial_state)
        state = result.state  # Final state after graph execution

        # If a task is newly created, link messages to it
        if state.task and associated_task is None:
            state.agent_answer.task_id = state.task.task_id
            state.user_query.task_id = state.task.task_id
            await self.message_repository.save(state.user_query)

        # Update task history if applicable
        if state.task is not None:
            state.task.history.append(state.user_query.message_id)
            state.task.history.append(state.agent_answer.message_id)
            await self.task_repository.save(state.task)

        await self.message_repository.save(state.agent_answer)
        return result.state

    async def stream(
        self,
        conversation: Conversation,
        message: Message,
        associated_task: Task | None = None,
    ) -> AsyncGenerator[Any, None]:  # TODO: Specify proper type
        yield
