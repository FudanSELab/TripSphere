import asyncio
import logging
import os
import warnings

from google.adk.agents import LlmAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.load_memory_tool import load_memory_tool
from httpx import AsyncClient

from chat.config.settings import get_settings
from chat.nacos.ai import NacosAI
from chat.prompts.agent import DELEGATOR_INSTRUCTION

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module="google.adk")

logger = logging.getLogger(__name__)

# Default remote agent names to discover via Nacos
_DEFAULT_REMOTE_AGENTS = ("order_assistant", "review_summary")


def _ensure_openai_env() -> None:
    """Ensure OpenAI environment variables are set from application settings."""
    openai_settings = get_settings().openai
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = openai_settings.api_key.get_secret_value()
    if not os.environ.get("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = openai_settings.base_url


async def _add_session_to_memory(callback_context: CallbackContext) -> None:
    await callback_context.add_session_to_memory()


class AgentFacadeFactory:
    """Factory that assembles a root LlmAgent with discovered remote sub-agents.

    The factory handles:
    - OpenAI environment variable configuration
    - Remote A2A agent discovery via Nacos
    - Root LlmAgent construction with tools and sub-agents

    Usage::

        factory = AgentFacadeFactory(httpx_client, nacos_ai)
        root_agent = await factory.create_agent()
    """

    def __init__(
        self,
        httpx_client: AsyncClient,
        nacos_ai: NacosAI,
        *,
        model: str = "openai/gpt-4o",
        remote_agent_names: list[str] | None = None,
    ) -> None:
        self._httpx_client = httpx_client
        self._nacos_ai = nacos_ai
        self._model = model
        self._remote_agent_names = list[str](
            remote_agent_names or _DEFAULT_REMOTE_AGENTS
        )

    async def create_facade(self) -> LlmAgent:
        """Assemble and return the root LlmAgent with remote sub-agents.

        This is the main factory method. It discovers remote A2A agents via
        Nacos, configures OpenAI environment variables, and constructs the
        root delegator agent.
        """
        _ensure_openai_env()
        sub_agents = await self._discover_remote_agents()
        # NOTE: McpToolset with StdioConnectionParams cannot be used with AG-UI ADK
        # because it contains TextIOWrapper instances that cannot be deep copied.
        # weather_toolset = McpToolset(
        #     connection_params=StdioConnectionParams(
        #         server_params=StdioServerParameters(
        #             command="python", args=["-m", "mcp_weather_server"]
        #         )
        #     )
        # )
        return LlmAgent(
            name="agent_facade",
            model=LiteLlm(model=self._model),
            instruction=DELEGATOR_INSTRUCTION,
            tools=[load_memory_tool],
            sub_agents=sub_agents,
            after_agent_callback=_add_session_to_memory,
        )

    async def _discover_remote_agents(self) -> list[BaseAgent]:
        """Discover and resolve all configured remote A2A agents concurrently."""
        tasks: list[asyncio.Task[RemoteA2aAgent | None]] = []
        async with asyncio.TaskGroup() as group:
            for name in self._remote_agent_names:
                tasks.append(group.create_task(self._resolve_remote_agent(name)))
        return [agent for task in tasks if (agent := task.result()) is not None]

    async def _resolve_remote_agent(self, agent_name: str) -> RemoteA2aAgent | None:
        """Resolve a single remote agent by name via Nacos agent discovery."""
        try:
            agent_card = await self._nacos_ai.get_agent_card(agent_name)
        except Exception:
            logger.exception("Failed to resolve remote agent '%s'", agent_name)
            return None
        return RemoteA2aAgent(
            name=agent_card.name,
            agent_card=agent_card,
            httpx_client=self._httpx_client,
            after_agent_callback=_add_session_to_memory,
        )
