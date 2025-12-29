from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from review_summary.vector_stores.reviews import ReviewVectorStore


async def bootstrap(client: AsyncQdrantClient, vector_dim: int = 3072) -> None:
    """Bootstrap Qdrant collections needed for review summary service."""
    if (await client.collection_exists(ReviewVectorStore.COLLECTION_NAME)) is False:
        await client.create_collection(
            collection_name=ReviewVectorStore.COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )
