import logging
from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppSettings(BaseModel):
    name: str = Field(default="trip-itinerary-planner")


class NacosSettings(BaseModel):
    enabled: bool = Field(default=True)
    server_address: str = Field(default="localhost:8848")
    namespace_id: str = Field(default="public")
    group_name: str = Field(default="DEFAULT_GROUP")


class OpenAISettings(BaseModel):
    api_key: SecretStr = Field(default=SecretStr("api-key"))
    base_url: str = Field(default="https://api.openai.com/v1")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env.development", ".env"],
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )
    app: AppSettings = Field(default_factory=AppSettings)
    nacos: NacosSettings = Field(default_factory=NacosSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug(f"{get_settings()}")
