import random
from collections.abc import Collection
from typing import Self

from v2.nacos import (  # type: ignore
    ClientConfigBuilder,
    DeregisterInstanceParam,
    Instance,
    ListInstanceParam,
    NacosNamingService,
    RegisterInstanceParam,
)  # pyright: ignore[reportMissingTypeStubs]

from review_summary.infra.nacos.utils import get_local_ip


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
        self.naming_service: NacosNamingService | None = None
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
        if self.naming_service is None:
            raise RuntimeError("Nacos naming service is not initialized")
        await self.naming_service.register_instance(
            request=RegisterInstanceParam(
                ip=self.ip,
                port=self.port,
                service_name=self.service_name,
                ephemeral=ephemeral,
            )
        )

    async def deregister(self, ephemeral: bool = True) -> None:
        if self.naming_service is None:
            raise RuntimeError("Nacos naming service is not initialized")
        await self.naming_service.deregister_instance(
            request=DeregisterInstanceParam(
                ip=self.ip,
                port=self.port,
                service_name=self.service_name,
                ephemeral=ephemeral,
            )
        )

    async def shutdown(self) -> None:
        if self.naming_service is None:
            return
        try:
            await self.naming_service.shutdown()
        except TypeError:
            # nacos-sdk-python 3.0 may await None while stopping internal tasks.
            pass
        finally:
            self.naming_service = None

    async def get_service_instance(
        self,
        service_name: str,
        required_metadata: Collection[str] = (),
    ) -> Instance:
        if self.naming_service is None:
            raise RuntimeError("Nacos naming service is not initialized")

        instances = await self.naming_service.list_instances(
            ListInstanceParam(service_name=service_name, healthy_only=True)
        )
        eligible_instances = [
            instance
            for instance in instances
            if instance.healthy
            and instance.enabled
            and instance.weight > 0
            and all(
                (instance.metadata or {}).get(key) for key in required_metadata
            )
        ]
        if not eligible_instances:
            metadata_requirement = (
                f" with metadata {sorted(required_metadata)}"
                if required_metadata
                else ""
            )
            raise RuntimeError(
                f"No healthy {service_name} instance found{metadata_requirement}"
            )
        return random.choice(eligible_instances)
