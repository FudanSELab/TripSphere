from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    name: str = Field(default="trip-review-summary")
    debug: bool = Field(default=False)


class UvicornSettings(BaseModel):
    """Loaded from environment variables:
    - UVICORN_HOST
    - UVICORN_PORT
    """

    host: str = Field(default="0.0.0.0", frozen=True)
    port: int = Field(default=24212, frozen=True)


class NacosSettings(BaseModel):
    server_address: str = Field(default="localhost:8848")
    namespace_id: str = Field(default="public")
    group_name: str = Field(default="DEFAULT_GROUP")


class QdrantSettings(BaseModel):
    url: str = Field(default="http://localhost:6333")
    database: str = Field(default="review_summary_db")


class Neo4jSettings(BaseModel):
    uri: str = Field(default="neo4j://localhost:7687")
    username: str = Field(default="neo4j")
    password: SecretStr = Field(default=SecretStr("password"))


class RocketmqSettings(BaseModel):
    endpoints: str = Field(default="localhost:8081")


class OpenAISettings(BaseModel):
    api_key: SecretStr = Field(default=SecretStr("api-key"))
    base_url: str = Field(default="https://api.openai.com/v1")


class LogSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    file: bool = Field(default=False)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.upper()
        return value


class CelerySettings(BaseModel):
    broker_url: str = Field(default="redis://localhost:6379/0")
    result_backend: str = Field(default="redis://localhost:6379/0")


class MinioSettings(BaseModel):
    endpoint: str = Field(default="localhost:9000")
    access_key: str = Field(default="access_key")
    secret_key: SecretStr = Field(default=SecretStr("secret_key"))

class Attraction_serviceSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=9006)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env.development", ".env"],
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )
    app: AppSettings = Field(default_factory=AppSettings)
    uvicorn: UvicornSettings = Field(default_factory=UvicornSettings)
    nacos: NacosSettings = Field(default_factory=NacosSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    rocketmq: RocketmqSettings = Field(default_factory=RocketmqSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    log: LogSettings = Field(default_factory=LogSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)
    attraction_service: Attraction_serviceSettings = Field(default_factory=Attraction_serviceSettings)

    def model_post_init(self, _: Any) -> None:
        if self.app.debug is True:
            self.log.level = "DEBUG"


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
