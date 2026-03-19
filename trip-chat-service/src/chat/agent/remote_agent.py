import asyncio
import logging
import warnings

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from chat.nacos.ai import NacosAI

# Suppress ADK Experimental Warnings
warnings.filterwarnings("ignore", module=".*")

logger = logging.getLogger(__name__)


# async def _add_session_to_memory(callback_context: CallbackContext) -> None:
#     await callback_context.add_session_to_memory()


class RemoteAgentsFactory:
    # Default remote agent names to discover via Nacos
    _DEFAULT_REMOTE_AGENTS = ["order_assistant"]

    def __init__(
        self, nacos_ai: NacosAI, *, remote_agents: list[str] | None = None
    ) -> None:
        self._nacos_ai = nacos_ai
        self._remote_agent_names = remote_agents or self._DEFAULT_REMOTE_AGENTS

    async def get_remote_agents(self) -> list[RemoteA2aAgent]:
        tasks: list[asyncio.Task[RemoteA2aAgent | None]] = []
        async with asyncio.TaskGroup() as group:
            for name in self._remote_agent_names:
                tasks.append(group.create_task(self._resolve_remote_agent(name)))
        return [agent for task in tasks if (agent := task.result()) is not None]

    async def _resolve_remote_agent(self, agent_name: str) -> RemoteA2aAgent | None:
        try:
            agent_card = await self._nacos_ai.get_agent_card(agent_name)
        except Exception:
            logger.exception("Failed to resolve remote agent '%s'", agent_name)
            return None
        logger.debug(f"Resolved remote agent '{agent_name}': {agent_card}")
        return RemoteA2aAgent(name=agent_card.name, agent_card=agent_card)
