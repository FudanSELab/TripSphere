from typing import Self, cast

from a2a.types import AgentCard
from v2.nacos import ClientConfigBuilder  # type: ignore
from v2.nacos.ai.nacos_ai_service import (  # type: ignore
    GetAgentCardParam,
    NacosAIService,
)


class NacosAI:
    def __init__(self, server_address: str) -> None:
        self.server_address = server_address
        self.client_config = (
            ClientConfigBuilder().server_address(self.server_address).build()
        )
        self.ai_service: NacosAIService | None = None

    @classmethod
    async def create_nacos_ai(cls, server_address: str) -> Self:
        instance = cls(server_address)
        instance.ai_service = await NacosAIService.create_ai_service(
            client_config=instance.client_config
        )
        return instance

    async def get_agent_card(
        self, agent_name: str, version: str | None = None
    ) -> AgentCard:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        agent_card = await self.ai_service.get_agent_card(
            GetAgentCardParam(agent_name=agent_name, version=version)
        )
        return cast(AgentCard, agent_card)

    async def shutdown(self) -> None:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        await self.ai_service.shutdown()
