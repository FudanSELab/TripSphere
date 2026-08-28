from typing import Any

from chat.config.settings import get_settings


def get_mem0_config() -> dict[str, Any]:
    settings = get_settings()
    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "chat_memories",
                "url": settings.qdrant.url,
                "embedding_model_dims": 3072,
            },
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-5.5",
                "temperature": 0.1,
                "api_key": settings.openai.api_key.get_secret_value(),
                "openai_base_url": settings.openai.base_url,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-large",
                "embedding_dims": 3072,
                "api_key": settings.openai.api_key.get_secret_value(),
                "openai_base_url": settings.openai.base_url,
            },
        },
        # "reranker": {
        #     "provider": "cohere",
        #     "config": {"model": "rerank-english-v3.0"},
        # },
    }
