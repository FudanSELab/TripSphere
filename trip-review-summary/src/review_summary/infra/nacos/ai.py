from typing import Self

from v2.nacos import ClientConfigBuilder  # type: ignore
from v2.nacos.ai.model.ai_constant import AIConstants  # type: ignore
from v2.nacos.ai.model.ai_param import (  # type: ignore
    DeregisterMcpServerEndpointParam,
    GetMcpServerParam,
    McpEndpointSpec,
    McpServerBasicInfo,
    McpToolSpecification,
    RegisterMcpServerEndpointParam,
    ReleaseMcpServerParam,
)
from v2.nacos.ai.model.mcp.mcp import McpCapability, McpTool  # type: ignore
from v2.nacos.ai.model.mcp.registry import ServerVersionDetail  # type: ignore
from v2.nacos.ai.nacos_ai_service import NacosAIService  # type: ignore

from review_summary.infra.nacos.utils import get_local_ip


class NacosAI:
    """Nacos AI registry client for the Review Summary MCP server."""

    def __init__(
        self,
        mcp_name: str,
        port: int,
        server_address: str,
        namespace_id: str,
        version: str,
    ) -> None:
        self.server_address = server_address
        self.namespace_id = namespace_id
        self.client_config = (
            ClientConfigBuilder()
            .server_address(server_address)
            .namespace_id(namespace_id)
            .build()
        )
        self.ai_service: NacosAIService | None = None
        self.mcp_name = mcp_name
        self.ip = get_local_ip()
        self.port = port
        self.version = version

    @classmethod
    async def create_nacos_ai(
        cls,
        mcp_name: str,
        port: int,
        server_address: str,
        namespace_id: str,
        version: str,
    ) -> Self:
        instance = cls(mcp_name, port, server_address, namespace_id, version)
        instance.ai_service = await NacosAIService.create_ai_service(
            client_config=instance.client_config
        )
        return instance

    async def register_mcp_server(self) -> None:
        service = self._require_service()
        await service.release_mcp_server(
            ReleaseMcpServerParam(
                server_spec=McpServerBasicInfo(
                    name=self.mcp_name,
                    protocol="streamable",
                    frontProtocol="streamable",
                    versionDetail=ServerVersionDetail(
                        version=self.version,
                        is_latest=True,
                    ),
                    capabilities=[McpCapability.TOOL],
                ),
                tool_spec=McpToolSpecification(
                    tools=[
                        McpTool(
                            name="summarize_reviews",
                            description=(
                                "Answer a question from reviews for the mounted target."
                            ),
                            inputSchema={
                                "type": "object",
                                "properties": {"query": {"type": "string"}},
                                "required": ["query"],
                            },
                        )
                    ]
                ),
                mcp_endpoint_spec=McpEndpointSpec(
                    type=AIConstants.MCP_ENDPOINT_TYPE_DIRECT,
                    data={
                        "address": self.ip,
                        "port": str(self.port),
                    },
                ),
            )
        )
        await service.register_mcp_server_endpoint(
            RegisterMcpServerEndpointParam(
                mcp_name=self.mcp_name,
                address=self.ip,
                port=self.port,
                version=self.version,
            )
        )

    async def deregister_mcp_server(self) -> None:
        service = self._require_service()
        param = DeregisterMcpServerEndpointParam(
            mcp_name=self.mcp_name,
            address=self.ip,
            port=self.port,
        )
        deregister = getattr(service, "deregister_mcp_server_endpoint", None)
        if deregister is not None:
            await deregister(param)
            return
        await service.grpc_client_proxy.deregister_mcp_server_endpoint(
            self.mcp_name, self.ip, self.port
        )

    async def get_mcp_server(self, version: str | None = None):
        return await self._require_service().get_mcp_server(
            GetMcpServerParam(mcp_name=self.mcp_name, version=version or self.version)
        )

    async def shutdown(self) -> None:
        if self.ai_service is None:
            return
        try:
            await self.ai_service.shutdown()
        finally:
            self.ai_service = None

    def _require_service(self) -> NacosAIService:
        if self.ai_service is None:
            raise RuntimeError("Nacos AI service is not initialized")
        return self.ai_service
