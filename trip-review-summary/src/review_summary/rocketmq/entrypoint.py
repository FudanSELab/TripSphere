import logging

from qdrant_client import AsyncQdrantClient

from review_summary.config.settings import get_settings
from review_summary.rocketmq.consumer import RocketMQConsumer
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for RocketMQ Consumer."""
    settings = get_settings()
    logger.info(f"Starting RocketMQ Consumer with settings: {settings}")

    # Initialize dependencies
    qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    vector_store = await TextUnitVectorStore.create_vector_store(
        client=qdrant_client, vector_dim=3072
    )
    consumer = RocketMQConsumer(text_unit_vector_store=vector_store)

    try:
        await consumer.startup()
        # Run the SimpleConsumer loop (will run until stopped)
        await consumer.run()
    finally:
        await consumer.shutdown()
        await qdrant_client.close()
        logger.info("RocketMQ Consumer shutdown complete")
