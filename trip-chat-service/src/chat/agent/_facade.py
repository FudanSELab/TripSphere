import asyncio
import json
import logging
from typing import AsyncGenerator, Self

from a2a.client import A2ACardResolver
from a2a.client import ClientConfig as A2AClientConfig
from a2a.client import ClientFactory as A2AClientFactory
from a2a.types import TransportProtocol
from httpx import AsyncClient
from pydantic import BaseModel
from pydantic_ai import Agent, ModelSettings, RunContext, Tool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from chat.agent._context import ContextProvider
from chat.agent._remote import RemoteA2aAgent
from chat.config.settings import get_settings
from chat.conversation.models import Conversation, Message
from chat.infra.nacos.naming import NacosNaming
from chat.prompts.agent import DELEGATOR_INSTRUCTION

logger = logging.getLogger(__name__)


class AgentFacadeDeps(BaseModel):
    conversation_id: str


class AgentFacade:
    """
    The orchestrator for scheduling agents and delegating tasks.
    """

    def __init__(
        self, httpx_client: AsyncClient, context_provider: ContextProvider | None = None
    ) -> None:
        self.httpx_client = httpx_client
        self.context_provider = context_provider
        a2a_client_config = A2AClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.a2a_client_factory = A2AClientFactory(a2a_client_config)
        self.remote_a2a_agents: dict[str, RemoteA2aAgent] = {}
        self.root_agent: Agent[AgentFacadeDeps] | None = None

    async def _resolve_base_url(self, base_url: str) -> None:
        card_resolver = A2ACardResolver(self.httpx_client, base_url)
        agent_card = await card_resolver.get_agent_card()
        remote_a2a_agent = RemoteA2aAgent(agent_card, self.a2a_client_factory)
        self.remote_a2a_agents[agent_card.name] = remote_a2a_agent

    async def _post_init(self, remote_agent_urls: list[str]) -> None:
        async with asyncio.TaskGroup() as group:
            for base_url in remote_agent_urls:
                group.create_task(self._resolve_base_url(base_url))

        openai_settings = get_settings().openai
        chat_model = OpenAIChatModel(
            model_name="gpt-4o-mini",  # TODO: Make configurable
            provider=OpenAIProvider(
                base_url=openai_settings.base_url,
                api_key=openai_settings.api_key.get_secret_value(),
            ),
            settings=ModelSettings(temperature=0.0),
        )

        self.root_agent = Agent[AgentFacadeDeps](
            model=chat_model,
            instructions=self._root_instructions,
            deps_type=AgentFacadeDeps,
            tools=[Tool(self.delegate_to_agent, takes_ctx=True)],
            instrument=True,
        )

    def _remote_agents(self) -> list[dict[str, str]]:
        if not self.remote_a2a_agents:
            return []  # No remote agents available

        remote_agents_info: list[dict[str, str]] = []
        for a2a_agent in self.remote_a2a_agents.values():
            agent_card = a2a_agent.agent_card
            logger.debug(f"Found registered A2A agent: {agent_card.name}.")
            agent_info = {
                "name": agent_card.name,
                "description": agent_card.description,
            }
            remote_agents_info.append(agent_info)
        return remote_agents_info

    def _root_instructions(self, ctx: RunContext[AgentFacadeDeps]) -> str:
        remote_agents_info = self._remote_agents()
        agents_info = [json.dumps(agent) for agent in remote_agents_info]
        agents = "\n".join(agents_info)
        return DELEGATOR_INSTRUCTION.format(agents=agents)

    @classmethod
    async def create_facade(
        cls,
        httpx_client: AsyncClient,
        nacos_naming: NacosNaming,
        context_provider: ContextProvider | None = None,
    ) -> Self:
        instance = cls(httpx_client, context_provider=context_provider)
        # TODO: Remote A2A agents discovery through Nacos
        await instance._post_init(["http://localhost:8000"])
        # await instance._post_init(remote_agent_urls=[])
        return instance

    async def invoke(self, conversation: Conversation, query: Message) -> Message:
        raise NotImplementedError

    async def stream(
        self, conversation: Conversation, query: Message
    ) -> AsyncGenerator[str, None]:
        if self.root_agent is None:
            raise RuntimeError("Root agent is not initialized.")
        yield ""

    async def delegate_to_agent(
        self, ctx: RunContext[AgentFacadeDeps], agent_name: str
    ) -> AsyncGenerator[None, None]:
        """
        Delegate the task to another agent.

        Arguments:
            agent_name: Name of the agent to delegate task to.

        Returns:
            TODO
        """
        raise NotImplementedError
