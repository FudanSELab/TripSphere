import logging
from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class MongoSettings(BaseModel):
    uri: str = Field(default="mongodb://root:fudanse@localhost:27017")


class PostgresSettings(BaseModel):
    dsn: str = Field(
        default="postgresql://postgres:fudanse@localhost:5432/inventory_db"
    )


class ImporterSettings(BaseModel):
    batch_size: int = Field(default=500, ge=1, description="Documents per batch")
    create_indexes: bool = Field(
        default=True,
        description=(
            "Whether indexes should be created after import "
            "(MongoDB only; ignored by PostgreSQL)"
        ),
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env.development", ".env"],
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        extra="ignore",
    )

    mongo: MongoSettings = Field(default_factory=MongoSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    importer: ImporterSettings = Field(default_factory=ImporterSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    logger.debug(f"Get settings: {settings}")
    return settings
