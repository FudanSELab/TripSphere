import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Self

from a2a.client import A2ACardResolver
from a2a.client import ClientConfig as A2AClientConfig
from a2a.client import ClientFactory as A2AClientFactory
from a2a.types import AgentCard, TransportProtocol
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from httpx import AsyncClient

from chat.agent._context import ContextProvider
from chat.common.parts import Part
from chat.config.settings import get_settings
from chat.conversation.models import Author, Conversation, Message
from chat.infra.nacos.naming import NacosNaming
from chat.prompts.agent import DELEGATOR_INSTRUCTION

logger = logging.getLogger(__name__)

_openai_settings = get_settings().openai
os.environ["OPENAI_API_KEY"] = _openai_settings.api_key.get_secret_value()
os.environ["OPENAI_BASE_URL"] = _openai_settings.base_url

session_service = InMemorySessionService()  # type: ignore


class AgentFacade:
    """
    The orchestrator for scheduling agents and delegating tasks.
    """

    def __init__(
        self, httpx_client: AsyncClient, context_provider: ContextProvider | None = None
    ) -> None:
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
        self.context_provider = context_provider
        self.root_agent: LlmAgent | None = None
        self.runner: Runner | None = None

    async def _post_init(self, agent_base_urls: list[str]) -> None:
        async with asyncio.TaskGroup() as group:
            for base_url in agent_base_urls:
                group.create_task(self._resolve_base_url(base_url))

        self.root_agent = LlmAgent(
            model=LiteLlm(model="openai/gpt-4o-mini"),
            name="agent_facade",
            instruction=DELEGATOR_INSTRUCTION,
            sub_agents=list(self.remote_a2a_agents.values()),
        )
        self.runner = Runner(
            app_name="chat-service",
            agent=self.root_agent,
            session_service=session_service,
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
        context_provider: ContextProvider | None = None,
    ) -> Self:
        instance = cls(httpx_client, context_provider=context_provider)
        # TODO: Remote agents discovery through Nacos
        await instance._post_init(["http://localhost:8000"])
        # await instance._post_init(remote_agent_urls=[])
        return instance

    async def invoke(self, conversation: Conversation, user_query: Message) -> Message:
        session = await session_service.get_session(
            app_name="chat-service",
            user_id=conversation.user_id,
            session_id=conversation.conversation_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name="chat-service",
                user_id=conversation.user_id,
                session_id=conversation.conversation_id,
            )

        if self.runner is None:
            raise RuntimeError("Runner is not initialized.")

        content = types.Content(
            role="user", parts=[types.Part(text=user_query.text_content())]
        )
        logger.debug(f"--- Running Query: {user_query.text_content()} ---")
        final_response_text = "No final text response captured."
        async for event in self.runner.run_async(
            user_id=conversation.user_id,
            session_id=conversation.conversation_id,
            new_message=content,
        ):
            logger.debug(f"Event ID: {event.id}, Author: {event.author}")

            # --- Check for specific parts FIRST ---
            has_specific_part = False
            if event.content and event.content.parts:
                for part in event.content.parts:  # Iterate through all parts
                    if part.executable_code:
                        # Access the actual code string via .code
                        logger.debug(
                            "    Agent generated code:\n"
                            f"```python\n{part.executable_code.code}\n```"
                        )
                        has_specific_part = True
                    elif part.code_execution_result:
                        # Access outcome and output correctly
                        logger.debug(
                            "    Code Execution Result: "
                            f"{part.code_execution_result.outcome}"
                            f" - Output:\n{part.code_execution_result.output}"
                        )
                        has_specific_part = True
                    # Also print any text parts found in any event for debugging
                    elif part.text and not part.text.isspace():
                        logger.debug(f"    Text: '{part.text.strip()}'")
                        # Do not set has_specific_part=True here,
                        # as we want the final response logic below

            # --- Check for final response AFTER specific parts ---
            # Only consider it final if it doesn't have the
            # specific code parts we just handled
            if not has_specific_part and event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    final_response_text = event.content.parts[0].text.strip()
                    logger.debug(f"==> Final Agent Response: {final_response_text}")
                else:
                    logger.debug(
                        "==> Final Agent Response: [No text content in final event]"
                    )

        return Message(
            conversation_id=conversation.conversation_id,
            author=Author.agent(),
            content=[Part.from_text(final_response_text)],
        )

    async def stream(
        self, conversation: Conversation, user_query: Message
    ) -> AsyncGenerator[Any, None]:  # TODO: Specify a proper type
        if self.root_agent is None:
            raise RuntimeError("Root agent is not initialized.")

        yield ""  # TODO
