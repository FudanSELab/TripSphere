from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ...


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()