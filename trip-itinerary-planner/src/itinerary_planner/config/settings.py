import logging
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    name: str = Field(default="trip-itinerary-planner")
    debug: bool = Field(default=False)


class UvicornSettings(BaseModel):
    """Loaded from environment variables:
    - UVICORN_HOST
    - UVICORN_PORT
    """

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=24215)


class NacosSettings(BaseModel):
    enabled: bool = Field(default=True)
    server_address: str = Field(default="localhost:8848")
    namespace_id: str = Field(default="public")
    group_name: str = Field(default="DEFAULT_GROUP")


class AmapSettings(BaseModel):
    """Loaded from the required AMAP_KEY environment variable."""

    key: SecretStr

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: SecretStr) -> SecretStr:
        key = value.get_secret_value().strip()
        if not key:
            raise ValueError("AMAP_KEY must not be empty")
        return SecretStr(key)


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
    amap: AmapSettings
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    log: LogSettings = Field(default_factory=LogSettings)

    def model_post_init(self, _: Any) -> None:
        if self.app.debug is True:
            self.log.level = "DEBUG"


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    # Pydantic Settings injects required fields from the environment at runtime.
    return Settings()  # type: ignore[call-arg]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug(f"{get_settings()}")
