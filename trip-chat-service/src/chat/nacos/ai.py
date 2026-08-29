from typing import Self, cast

from a2a.types import AgentCard
from v2.nacos import ClientConfigBuilder  # type: ignore
from v2.nacos.ai.nacos_ai_service import (  # type: ignore
    GetAgentCardParam,
    GetMcpServerParam,
    NacosAIService,
)


class NacosAI:
    def __init__(self, server_address: str, namespace_id: str = "public") -> None:
        self.server_address = server_address
        self.client_config = (
            ClientConfigBuilder()
            .server_address(self.server_address)
            .namespace_id(namespace_id)
            .build()
        )
        self.ai_service: NacosAIService | None = None

    @classmethod
    async def create_nacos_ai(
        cls, server_address: str, namespace_id: str = "public"
    ) -> Self:
        instance = cls(server_address, namespace_id)
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

    async def get_mcp_server(self, mcp_name: str, version: str | None = None):
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        return await self.ai_service.get_mcp_server(
            GetMcpServerParam(mcp_name=mcp_name, version=version)
        )

    async def shutdown(self) -> None:
        if self.ai_service is None:
            return
        try:
            await self.ai_service.shutdown()
        finally:
            self.ai_service = None
