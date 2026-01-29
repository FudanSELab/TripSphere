import asyncio
import json
import logging
import os
import warnings
from functools import lru_cache
from typing import Any, AsyncGenerator, Self

import a2a.types
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.tools.load_memory_tool import load_memory_tool
from google.genai import types
from httpx import AsyncClient
from mem0 import AsyncMemory  # type: ignore
from pymongo import AsyncMongoClient

from chat.agent.memory import Mem0MemoryService
from chat.agent.session import MongoSessionService
from chat.common.parts import Part
from chat.config.settings import get_settings
from chat.infra.nacos.ai import NacosAI
from chat.internal.models import Author, Conversation, Message
from chat.prompts.agent import DELEGATOR_INSTRUCTION

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module="google.adk")

logger = logging.getLogger(__name__)


async def _add_session_to_memory_callback(callback_context: CallbackContext) -> None:
    await callback_context.add_session_to_memory()


@lru_cache(maxsize=1, typed=True)
def get_root_agent(model: str = "openai/gpt-4o-mini") -> LlmAgent:
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY", None):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL", None):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url

    return LlmAgent(
        name="agent_facade",
        model=LiteLlm(model=model),
        instruction=DELEGATOR_INSTRUCTION,
        tools=[load_memory_tool],
        after_agent_callback=_add_session_to_memory_callback,
    )


class AgentFacade:
    """Orchestrator for scheduling agents and delegating tasks."""

    def __init__(
        self,
        httpx_client: AsyncClient,
        nacos_ai: NacosAI,
        mongo_client: AsyncMongoClient[dict[str, Any]],
        memory_engine: AsyncMemory,
    ) -> None:
        self.httpx_client = httpx_client
        self.nacos_ai = nacos_ai
        self.remote_a2a_agents: dict[str, RemoteA2aAgent] = {}
        self.agent_cards: dict[str, a2a.types.AgentCard] = {}
        self.session_service = MongoSessionService(mongo_client)
        self.memory_service = Mem0MemoryService(memory_engine)
        self.default_runner: Runner | None = None
        self.app_name = get_settings().app.name

    async def _post_init(self, agent_names: list[str]) -> None:
        async with asyncio.TaskGroup() as group:
            for agent_name in agent_names:
                group.create_task(self._resolve_agent_name(agent_name))

        self.default_runner = Runner(
            app_name=self.app_name,
            agent=get_root_agent().clone(
                {"sub_agents": list[RemoteA2aAgent](self.remote_a2a_agents.values())}
            ),
            session_service=self.session_service,
            memory_service=self.memory_service,
        )

    async def _resolve_agent_name(self, agent_name: str) -> None:
        try:
            agent_card = await self.nacos_ai.get_agent_card(agent_name)
        except Exception as e:
            logger.error(f"Failed to resolve agent name {agent_name}: {e}")
            return None  # Fail silently for now
        self.agent_cards[agent_card.name] = agent_card
        self.remote_a2a_agents[agent_card.name] = RemoteA2aAgent(
            name=agent_card.name,
            agent_card=agent_card,
            httpx_client=self.httpx_client,
            after_agent_callback=_add_session_to_memory_callback,
        )

    @classmethod
    async def create_facade(
        cls,
        httpx_client: AsyncClient,
        nacos_ai: NacosAI,
        mongo_client: AsyncMongoClient[dict[str, Any]],
        memory_engine: AsyncMemory,
    ) -> Self:
        instance = cls(httpx_client, nacos_ai, mongo_client, memory_engine)
        # Remote A2A agents discovery through Nacos AI service
        await instance._post_init(["journey_assistant", "review_summary"])
        return instance

    async def invoke(self, conversation: Conversation, user_query: Message) -> Message:
        message: Message | None = None
        async for event in self.stream(conversation, user_query):
            if isinstance(event, Message):
                message = event
        if message is None:
            raise RuntimeError("No message returned from stream.")
        return message

    async def stream(
        self, conversation: Conversation, user_query: Message
    ) -> AsyncGenerator[Event | Message, None]:
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=conversation.user_id,
            session_id=conversation.conversation_id,
        )
        if session is None:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=conversation.user_id,
                session_id=conversation.conversation_id,
            )

        # Extract metadata (target_id, target_type, etc.) for A2A agents
        metadata: dict[str, Any] = {}
        if user_query.metadata:
            for key in ("target_id", "target_type"):
                if key in user_query.metadata:
                    metadata[key] = user_query.metadata[key]
        part = types.Part(
            text=user_query.text_content(),
            inline_data=(
                types.Blob(
                    data=json.dumps(metadata).encode("utf-8"),
                    mime_type="application/json",
                )
                if metadata
                else None
            ),
        )
        user_content = types.Content(role="user", parts=[part])

        logger.debug(f"==> Running Query: {user_content.model_dump()}")

        # Check if user specified a target agent
        agent = user_query.metadata.get("agent") if user_query.metadata else None
        if agent and isinstance(agent, str) and (agent in self.remote_a2a_agents):
            # Direct routing to the specified agent
            logger.debug(f"==> Direct routing to agent: {agent}")
            runner_to_use = Runner(
                app_name=self.app_name,
                agent=self.remote_a2a_agents[agent],
                session_service=self.session_service,
                memory_service=self.memory_service,
            )
        else:
            # Normal facade orchestration through root agent
            if self.default_runner is None:
                raise RuntimeError("Default runner is not initialized.")
            runner_to_use = self.default_runner

        full_response_text = ""
        final_text = "No final textual response received."  # Fallback message

        async for event in runner_to_use.run_async(
            user_id=conversation.user_id,
            session_id=conversation.conversation_id,
            new_message=user_content,
        ):
            # Reference: https://google.github.io/adk-docs/events/
            logger.debug(f"Event ID: {event.id}, author: {event.author}")

            if event.content and event.content.parts:
                if calls := event.get_function_calls():
                    logger.debug(
                        "    [Tool Call Request]: "
                        f"{[call.model_dump() for call in calls]}"
                    )
                elif resps := event.get_function_responses():
                    logger.debug(
                        f"    [Tool Result]: {[resp.model_dump() for resp in resps]}"
                    )
                elif text := event.content.parts[0].text:
                    if event.partial:
                        logger.debug(f"    [Streaming Text Chunk]: {text}")
                        full_response_text += text
                    else:
                        logger.debug(f"    [Complete Text Content]: {text}")
                else:
                    logger.debug("    [Other Content]: Such as code execution")

            elif event.actions:
                if event.actions.state_delta:
                    logger.debug(f"    [State Update]: {event.actions.state_delta}")
                if event.actions.artifact_delta:
                    logger.debug(
                        f"    [Artifact Update]: {event.actions.artifact_delta}"
                    )
                if event.actions.transfer_to_agent:
                    logger.debug(
                        f"    [Signal]: Transfer to {event.actions.transfer_to_agent}"
                    )
                if event.actions.escalate:
                    logger.debug("    [Signal]: Escalate (terminate loop)")
                if event.actions.skip_summarization:
                    logger.debug("    [Signal]: Skip summarization for tool result")

            else:
                logger.debug("    [Control Signal or Other]")

            # Check if it's a final, displayable event
            if event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    final_text = full_response_text + (
                        event.content.parts[0].text if not event.partial else ""
                    )
                    logger.debug(f"==> Text Response: {final_text.rstrip()}")
                    full_response_text = ""  # Reset the accumulator
                elif (
                    event.actions
                    and event.actions.skip_summarization
                    and event.get_function_responses()
                ):
                    response_data = event.get_function_responses()[0].response
                    logger.debug(f"==> Raw Tool Result: {response_data}")
                    final_text = str(response_data)
                elif (
                    hasattr(event, "long_running_tool_ids")
                    and event.long_running_tool_ids
                ):
                    logger.debug("==> Long Running Tool: Running in background...")
                    final_text = "Tool is running in background..."
                else:
                    logger.debug("==> Non-textual Response: No text to display")

            yield event

        yield Message(
            conversation_id=conversation.conversation_id,
            author=Author.agent("agent_facade"),
            content=[Part.from_text(final_text)],
        )
