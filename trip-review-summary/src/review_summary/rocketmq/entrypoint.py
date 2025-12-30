import logging

from qdrant_client import AsyncQdrantClient

from review_summary.config.settings import get_settings
from review_summary.infra.qdrant.bootstrap import bootstrap
from review_summary.rocketmq.consumer import RocketMQConsumer

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main entry point for RocketMQ Consumer."""
    settings = get_settings()
    logger.info(f"Starting RocketMQ Consumer with settings: {settings}")

    # Initialize dependencies
    qdrant_client = AsyncQdrantClient(url=settings.qdrant.url)
    await bootstrap(qdrant_client)

    consumer = RocketMQConsumer(qdrant_client=qdrant_client)

    try:
        await consumer.startup()
        # Run consumer loop (will run until stopped)
        await consumer.run()
    finally:
        await consumer.shutdown()
        await qdrant_client.close()
        logger.info("RocketMQ Consumer shutdown complete")
