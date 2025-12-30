from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from review_summary.vector_stores.text_unit import TextUnitVectorStore


async def bootstrap(client: AsyncQdrantClient, vector_dim: int = 3072) -> None:
    """Bootstrap Qdrant collections needed for review summary service."""
    if (await client.collection_exists(TextUnitVectorStore.COLLECTION_NAME)) is False:
        await client.create_collection(
            collection_name=TextUnitVectorStore.COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )
