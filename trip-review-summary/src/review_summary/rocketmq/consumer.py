import asyncio
import json
import logging
from typing import Any, cast

from rocketmq import (  # type: ignore
    ClientConfiguration,
    Credentials,
    FilterExpression,
    SimpleConsumer,
)
from rocketmq import Message as RocketmqMessage  # pyright: ignore

from review_summary.config.settings import get_settings
from review_summary.rocketmq.handlers import handle_create_review
from review_summary.rocketmq.typing import Message
from review_summary.vector_stores.text_unit import TextUnitVectorStore

logger = logging.getLogger(__name__)


class RocketMQConsumer:
    MAX_MESSAGE_NUM = 16
    INVISIBLE_DURATION = 15
    CONSUMER_GROUP = "ReviewSummaryConsumerGroup"
    TOPIC = "ReviewTopic"

    def __init__(self, text_unit_vector_store: TextUnitVectorStore) -> None:
        self.text_unit_vector_store = text_unit_vector_store
        self._running = False
        self._consumer: SimpleConsumer | None = None

    async def startup(self) -> None:
        """Initialize and start the RocketMQ consumer."""
        credentials = Credentials()
        rocketmq_settings = get_settings().rocketmq
        config = ClientConfiguration(rocketmq_settings.endpoints, credentials)
        self._consumer = SimpleConsumer(
            client_configuration=config,
            consumer_group=self.CONSUMER_GROUP,
            subscription={self.TOPIC: FilterExpression()},
        )
        # Startup is synchronous, run in thread pool
        await asyncio.to_thread(self._consumer.startup)
        self._running = True
        logger.info("RocketMQ consumer started")

    async def _process_message(self, message: Message) -> None:
        """Process a single message."""
        try:
            message_id = message.message_id
            if message.body is None:
                logger.warning(f"Empty message body for message ID: {message_id}")
                return  # For now, just skip empty messages
            message_body = cast(
                dict[str, Any], json.loads(message.body.decode("utf-8"))
            )
            logger.info(f"Processing message ID: {message_id}, tag: {message.tag}")

            match message.tag:
                case "CreateReview":
                    await handle_create_review(
                        self.text_unit_vector_store, message_body
                    )
                case "UpdateReview":
                    raise NotImplementedError
                case "DeleteReview":
                    raise NotImplementedError
                case _:
                    logger.warning(f"Unknown message tag: {message.tag}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def run(self) -> None:
        """Main consumer loop - receives and processes messages."""
        if self._consumer is None:
            raise RuntimeError("Consumer not started. Call start() first.")

        logger.info("RocketMQ consumer running")
        while self._running:
            try:
                # Receive messages in thread pool (RocketMQ SDK is synchronous)
                rmq_messages = cast(
                    list[RocketmqMessage],
                    await asyncio.to_thread(
                        self._consumer.receive,  # pyright: ignore
                        self.MAX_MESSAGE_NUM,
                        self.INVISIBLE_DURATION,
                    ),
                )

                if not rmq_messages:
                    continue  # No messages received, continue loop

                # Process messages sequentially to maintain order
                for rmq_message in rmq_messages:
                    if not self._running:
                        break  # Exit if stopping
                    try:
                        message = Message.from_rmq_message(rmq_message)
                        await self._process_message(message)
                    except Exception as e:
                        logger.error(f"Message processing error: {e}", exc_info=True)
                    finally:
                        # Acknowledge message after processing
                        await asyncio.to_thread(self._consumer.ack, rmq_message)

            except Exception as e:
                if self._running:  # Only log if not shutting down
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retry

        logger.info("RocketMQ consumer stopped")

    async def shutdown(self) -> None:
        """Stop the consumer gracefully."""
        logger.info("Stopping RocketMQ consumer...")
        self._running = False

        if self._consumer is not None:
            await asyncio.to_thread(self._consumer.shutdown)

        logger.info("RocketMQ consumer shutdown complete")
