from typing import Self

from v2.nacos import ClientConfigBuilder  # type: ignore
from v2.nacos.ai.model.ai_constant import AIConstants  # type: ignore
from v2.nacos.ai.model.ai_param import (  # type: ignore
    GetMcpServerParam,
    McpEndpointSpec,
    McpServerBasicInfo,
    McpToolSpecification,
    ReleaseMcpServerParam,
)
from v2.nacos.ai.model.mcp.mcp import (  # type: ignore
    McpServerRemoteServiceConfig,
    McpTool,
)
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
        service_name: str = "trip-review-summary",
        group_name: str = "DEFAULT_GROUP",
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
        self.service_name = service_name
        self.group_name = group_name

    @classmethod
    async def create_nacos_ai(
        cls,
        mcp_name: str,
        port: int,
        server_address: str,
        namespace_id: str,
        version: str,
        service_name: str = "trip-review-summary",
        group_name: str = "DEFAULT_GROUP",
    ) -> Self:
        instance = cls(
            mcp_name,
            port,
            server_address,
            namespace_id,
            version,
            service_name,
            group_name,
        )
        instance.ai_service = await NacosAIService.create_ai_service(
            client_config=instance.client_config
        )
        return instance

    async def register_mcp_server(self, path: str = "/mcp") -> None:
        service = self._require_service()
        try:
            await service.get_mcp_server(
                GetMcpServerParam(mcp_name=self.mcp_name, version=self.version)
            )
            return
        except Exception:
            pass
        await service.release_mcp_server(
            ReleaseMcpServerParam(
                server_spec=McpServerBasicInfo(
                    name=self.mcp_name,
                    protocol="mcp-streamable",
                    frontProtocol="mcp-streamable",
                    versionDetail=ServerVersionDetail(
                        version=self.version,
                        is_latest=True,
                    ),
                    remoteServerConfig=McpServerRemoteServiceConfig(
                        exportPath=path,
                    ),
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
                    type=AIConstants.MCP_ENDPOINT_TYPE_REF,
                    data={
                        "serviceName": self.service_name,
                        "groupName": self.group_name,
                        "namespaceId": self.namespace_id,
                    },
                ),
            )
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
