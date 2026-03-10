"""
Shared configuration module for the initializer.

This file centralizes the database connection settings and importer behavior
parameters shared by all importers (POI / hotel / attraction), making them
easy to maintain and extend.

Domain types (ImportMode, ImportStats) live in ``initializer.types`` and are
intentionally kept separate from configuration concerns.

If PostgreSQL import support is added later, each importer can simply reference
``PostgresSettings`` without requiring any structural change to this module.

Environment variable mapping (via pydantic-settings, using ``_`` as the nested
delimiter and splitting at most once):

    MONGO_URI                     -> settings.mongo.uri
    POSTGRES_DSN                  -> settings.postgres.dsn
    IMPORTER_BATCH_SIZE           -> settings.importer.batch_size
    IMPORTER_CREATE_INDEXES       -> settings.importer.create_indexes

You can also place ``.env.local`` or ``.env`` in the project root, and
pydantic-settings will load them in order automatically.
"""

from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Database connection settings
# ---------------------------------------------------------------------------


class MongoSettings(BaseModel):
    """
    MongoDB connection settings.

    Environment variable:
        MONGO_URI  - MongoDB connection string, defaulting to a local dev instance.
    """

    uri: str = Field(default="mongodb://root:fudanse@localhost:27017")


class PostgresSettings(BaseModel):
    """
    PostgreSQL connection settings reserved for future relational imports.

    Environment variable:
        POSTGRES_DSN  - PostgreSQL DSN connection string.

    Example DSNs::

        postgresql://user:password@localhost:5432/mydb
        postgresql+psycopg://user:password@localhost:5432/mydb
    """

    dsn: str = Field(default="postgresql://postgres:password@localhost:5432/postgres")


# ---------------------------------------------------------------------------
# Shared importer behavior settings
# ---------------------------------------------------------------------------


class ImporterSettings(BaseModel):
    """
    Behavior settings shared by all importers.

    Environment variables:
        IMPORTER_BATCH_SIZE      - Documents processed per batch, default 500.
        IMPORTER_CREATE_INDEXES  - Whether indexes should be created after
                                   import (MongoDB only), default true.
    """

    batch_size: int = Field(default=500, ge=1, description="Documents per batch")
    create_indexes: bool = Field(
        default=True,
        description=(
            "Whether indexes should be created after import "
            "(MongoDB only; ignored by PostgreSQL)"
        ),
    )


# ---------------------------------------------------------------------------
# Root Settings (aggregates all nested settings, supports env vars / .env files)
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """
    Root settings model for the initializer.

    Values are loaded from environment variables or .env files via
    pydantic-settings. The nested delimiter is ``_`` and splitting happens at
    most once to avoid incorrectly splitting underscores inside field names.
    """

    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],
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
    """Return the cached process-wide Settings instance."""
    return Settings()


# ---------------------------------------------------------------------------
# Quick debugging entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    s = get_settings()
    print(s.model_dump())


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__: list[Any] = [
    "MongoSettings",
    "PostgresSettings",
    "ImporterSettings",
    "Settings",
    "get_settings",
]
