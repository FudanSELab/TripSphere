from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoSettings(BaseModel):
    uri: str = Field(default="mongodb://localhost:27017")
    database: str = Field(default="review_summary_db")


class RocketmqSettings(BaseModel):
    namesrv_addr: str = Field(default="localhost:8081")


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
    mongo: MongoSettings = Field(default_factory=MongoSettings)
    rocketmq: RocketmqSettings = Field(default_factory=RocketmqSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
