from typing import Self

from a2a.types import AgentCard
from v2.nacos import ClientConfigBuilder  # type: ignore
from v2.nacos.ai.nacos_ai_service import (  # type: ignore
    DeregisterAgentEndpointParam,
    NacosAIService,
    RegisterAgentEndpointParam,
    ReleaseAgentCardParam,
)

from review_summary.infra.nacos.utils import get_local_ip


class NacosAI:
    def __init__(self, agent_name: str, port: int, server_address: str) -> None:
        self.server_address = server_address
        self.client_config = (
            ClientConfigBuilder().server_address(self.server_address).build()
        )
        self.ai_service: NacosAIService | None = None
        self.agent_name = agent_name
        self.ip = get_local_ip()
        self.port = port

    @classmethod
    async def create_nacos_ai(
        cls, agent_name: str, port: int, server_address: str
    ) -> Self:
        instance = cls(agent_name, port, server_address)
        instance.ai_service = await NacosAIService.create_ai_service(
            client_config=instance.client_config
        )
        return instance

    async def release_agent_card(self, agent_card: AgentCard) -> None:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        await self.ai_service.release_agent_card(
            ReleaseAgentCardParam(agent_card=agent_card, set_as_latest=True)
        )

    async def register(self, version: str) -> None:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        await self.ai_service.register_agent_endpoint(
            RegisterAgentEndpointParam(
                agent_name=self.agent_name,
                version=version,
                address=self.ip,
                port=self.port,
            )
        )

    async def deregister(self, version: str) -> None:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        await self.ai_service.deregister_agent_endpoint(
            DeregisterAgentEndpointParam(
                agent_name=self.agent_name,
                version=version,
                address=self.ip,
                port=self.port,
            )
        )

    async def shutdown(self) -> None:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        await self.ai_service.shutdown()
