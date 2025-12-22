from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoSettings(BaseModel):
    uri: str = Field(default="mongodb://localhost:27017")
    database: str = Field(default="review_summary_db")


class RocketmqSettings(BaseModel):
    namesrv_addr: str = Field(default="localhost:8081")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env.development", ".env"],
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )
    mongo: MongoSettings = MongoSettings()
    rocketmq: RocketmqSettings = RocketmqSettings()


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
