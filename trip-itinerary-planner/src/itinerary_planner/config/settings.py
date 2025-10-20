import logging

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from itinerary_planner.config.defaults import defaults

logger = logging.getLogger(__name__)


class Service(BaseModel):
    name: str = Field(default=defaults.service.name)
    namespace: str = Field(default=defaults.service.namespace)


class Grpc(BaseModel):
    port: int = Field(default=defaults.grpc.port)


class Nacos(BaseModel):
    enabled: bool = Field(default=defaults.nacos.enabled)
    server_address: str = Field(default=defaults.nacos.server_address)
    namespace_id: str = Field(default=defaults.nacos.namespace_id)
    group_name: str = Field(default=defaults.nacos.group_name)


class LLM(BaseModel):
    model: str = Field(default=defaults.llm.model)
    temperature: float = Field(default=defaults.llm.temperature)
    max_tokens: int = Field(default=defaults.llm.max_tokens)
    api_key: SecretStr = Field(default=SecretStr(""))
    base_url: str | None = Field(default=defaults.llm.base_url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        cli_parse_args=True,
        env_file=".env",
        env_file_encoding="utf-8",
    )
    service: Service = Field(default_factory=Service)
    grpc: Grpc = Field(default_factory=Grpc)
    nacos: Nacos = Field(default_factory=Nacos)
    llm: LLM = Field(default_factory=LLM)


settings = Settings()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug(f"{settings}")
