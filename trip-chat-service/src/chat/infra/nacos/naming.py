import socket
from typing import Self

from v2.nacos import (
    ClientConfigBuilder,
    DeregisterInstanceParam,
    NacosNamingService,
    RegisterInstanceParam,
)


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return socket.gethostbyname(socket.gethostname())


class NacosNaming:
    def __init__(
        self, service_name: str, port: int, server_address: str, namespace_id: str
    ) -> None:
        self.server_address = server_address
        self.namespace_id = namespace_id
        self.client_config = (
            ClientConfigBuilder()
            .server_address(self.server_address)
            .namespace_id(self.namespace_id)
            .build()
        )
        self.naming_service: NacosNamingService
        self.service_name = service_name
        self.ip = get_local_ip()
        self.port = port

    @classmethod
    async def create_naming(
        cls, service_name: str, port: int, server_address: str, namespace_id: str
    ) -> Self:
        instance = cls(service_name, port, server_address, namespace_id)
        instance.naming_service = await NacosNamingService.create_naming_service(
            client_config=instance.client_config
        )
        return instance

    async def register(self, ephemeral: bool = True) -> None:
        await self.naming_service.register_instance(
            request=RegisterInstanceParam(
                ip=self.ip,
                port=self.port,
                service_name=self.service_name,
                ephemeral=ephemeral,
            )
        )

    async def deregister(self, ephemeral: bool = True) -> None:
        await self.naming_service.deregister_instance(
            request=DeregisterInstanceParam(
                ip=self.ip,
                port=self.port,
                service_name=self.service_name,
                ephemeral=ephemeral,
            )
        )
