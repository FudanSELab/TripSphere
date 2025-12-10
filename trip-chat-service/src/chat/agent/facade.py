import asyncio
import logging
import os
import warnings
from typing import Any, AsyncGenerator, Self

from a2a.client import A2ACardResolver
from a2a.client import ClientConfig as A2AClientConfig
from a2a.client import ClientFactory as A2AClientFactory
from a2a.types import AgentCard, TransportProtocol
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.genai import types
from httpx import AsyncClient
from pymongo import AsyncMongoClient

from chat.agent.session import MongoSessionService
from chat.common.parts import Part
from chat.config.settings import get_settings
from chat.conversation.models import Author, Conversation, Message
from chat.infra.nacos.naming import NacosNaming
from chat.prompts.agent import DELEGATOR_INSTRUCTION

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module="google.adk")

logger = logging.getLogger(__name__)

_openai_settings = get_settings().openai
os.environ["OPENAI_API_KEY"] = _openai_settings.api_key.get_secret_value()
os.environ["OPENAI_BASE_URL"] = _openai_settings.base_url

_root_agent = LlmAgent(
    name="agent_facade",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    instruction=DELEGATOR_INSTRUCTION,
)


class AgentFacade:
    """
    The orchestrator for scheduling agents and delegating tasks.
    """

    def __init__(self, httpx_client: AsyncClient) -> None:
        self.httpx_client = httpx_client
        a2a_client_config = A2AClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.a2a_client_factory = A2AClientFactory(a2a_client_config)
        self.remote_a2a_agents: dict[str, RemoteA2aAgent] = {}
        self.agent_cards: dict[str, AgentCard] = {}
        self.session_service: MongoSessionService | None = None
        self.runner: Runner | None = None

    async def _post_init(
        self, agent_base_urls: list[str], mongo_client: AsyncMongoClient[dict[str, Any]]
    ) -> None:
        async with asyncio.TaskGroup() as group:
            for base_url in agent_base_urls:
                group.create_task(self._resolve_base_url(base_url))

        self.session_service = MongoSessionService(mongo_client)
        self.runner = Runner(
            app_name="chat-service",
            agent=_root_agent.clone(
                {"sub_agents": list(self.remote_a2a_agents.values())}
            ),
            session_service=self.session_service,
        )

    async def _resolve_base_url(self, base_url: str) -> None:
        card_resolver = A2ACardResolver(self.httpx_client, base_url)
        agent_card = await card_resolver.get_agent_card()
        self.agent_cards[agent_card.name] = agent_card
        self.remote_a2a_agents[agent_card.name] = RemoteA2aAgent(
            name=agent_card.name, agent_card=agent_card
        )

    @classmethod
    async def create_facade(
        cls,
        httpx_client: AsyncClient,
        nacos_naming: NacosNaming,
        mongo_client: AsyncMongoClient[dict[str, Any]],
    ) -> Self:
        instance = cls(httpx_client)
        # TODO: Remote agents discovery through Nacos
        await instance._post_init(["http://localhost:8000"], mongo_client)
        return instance

    async def invoke(self, conversation: Conversation, user_query: Message) -> Message:
        raise NotImplementedError

    async def stream(
        self, conversation: Conversation, user_query: Message
    ) -> AsyncGenerator[Event | Message, None]:
        if self.session_service is None:
            raise RuntimeError("Session service is not initialized.")

        session = await self.session_service.get_session(
            app_name="chat-service",
            user_id=conversation.user_id,
            session_id=conversation.conversation_id,
        )
        if session is None:
            session = await self.session_service.create_session(
                app_name="chat-service",
                user_id=conversation.user_id,
                session_id=conversation.conversation_id,
            )

        if self.runner is None:
            raise RuntimeError("Runner is not initialized.")

        text_query = user_query.text_content()
        user_content = types.Content(role="user", parts=[types.Part(text=text_query)])

        logger.debug(f"==> Running Query: {text_query}")

        full_response_text = ""
        final_text = "No final textual response received."  # Fallback message
        async for event in self.runner.run_async(
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
