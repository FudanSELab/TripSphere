import socket

from v2.nacos import (
    ClientConfigBuilder,
    DeregisterInstanceParam,
    NacosNamingService,
    RegisterInstanceParam,
)

from itinerary.config.settings import settings


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except Exception:
        return socket.gethostbyname(socket.gethostname())


class NacosNaming:
    def __init__(self) -> None:
        self.client_config = (
            ClientConfigBuilder()
            .server_address(settings.nacos.server_address)
            .namespace_id(settings.nacos.namespace_id)
            .build()
        )
        self.service_name = settings.service.name
        self.ip = get_local_ip()
        self.port = settings.grpc.port

    async def register(self) -> None:
        naming_service = await NacosNamingService.create_naming_service(
            self.client_config
        )
        await naming_service.register_instance(
            request=RegisterInstanceParam(
                service_name=self.service_name, ip=self.ip, port=self.port
            )
        )

    async def deregister(self) -> None:
        naming_service = await NacosNamingService.create_naming_service(
            self.client_config
        )
        await naming_service.deregister_instance(
            request=DeregisterInstanceParam(
                service_name=self.service_name, ip=self.ip, port=self.port
            )
        )
