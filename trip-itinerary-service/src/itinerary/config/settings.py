import logging

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from itinerary.config.defaults import defaults

logger = logging.getLogger(__name__)


class Service(BaseModel):
    name: str = Field(default=defaults.service.name)
    namespace: str = Field(default=defaults.service.namespace)


class Grpc(BaseModel):
    port: int = Field(default=defaults.grpc.port)


class Nacos(BaseModel):
    server_address: str = Field(default=defaults.nacos.server_address)
    namespace_id: str = Field(default=defaults.nacos.namespace_id)
    group_name: str = Field(default=defaults.nacos.group_name)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", cli_parse_args=True)
    service: Service = Field(default_factory=Service)
    grpc: Grpc = Field(default_factory=Grpc)
    nacos: Nacos = Field(default_factory=Nacos)


settings = Settings()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug(f"{settings}")
