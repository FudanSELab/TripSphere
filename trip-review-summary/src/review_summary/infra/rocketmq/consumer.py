import asyncio
import json
import logging
import threading
from asyncio import AbstractEventLoop
from typing import Any

from rocketmq import (  # type: ignore
    ClientConfiguration,
    Credentials,
    FilterExpression,
    Message,
    SimpleConsumer,
)  # pyright: ignore[reportMissingTypeStubs]

from review_summary.config.settings import get_settings
from review_summary.index.embedding import text_to_embedding
from review_summary.index.repository import ReviewEmbedding, ReviewEmbeddingRepository

logger = logging.getLogger(__name__)


class RocketMQConsumer:
    CONSUMER_GROUP = "ReviewSummaryConsumerGroup"
    TOPIC = "ReviewTopic"
    MAX_MESSAGE_NUM = 16
    INVISIBLE_DURATION = 15
    MESSAGE_TIMEOUT_SECONDS = 10
    # MESSAGE_TIMEOUT + buffer for graceful shutdown
    SHUTDOWN_TIMEOUT_SECONDS = 15

    def __init__(self, repository: ReviewEmbeddingRepository) -> None:
        self.repository = repository

        # Initialize RocketMQ SimpleConsumer
        credentials = Credentials()
        rocketmq_settings = get_settings().rocketmq
        config = ClientConfiguration(rocketmq_settings.endpoints, credentials)
        self.consumer = SimpleConsumer(
            client_configuration=config,
            consumer_group=self.CONSUMER_GROUP,
            subscription={self.TOPIC: FilterExpression()},
        )
        self.consumer.startup()

        def _start_event_loop(loop: AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        # Initialize background event loop for async processing
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(
            target=_start_event_loop, args=(self.loop,), daemon=True
        )
        self.loop_thread.start()

        # Start consumer in a dedicated thread
        self._running = True
        self._consumer_thread = threading.Thread(target=self.run_consumer, daemon=True)
        self._consumer_thread.start()

    async def _consume(self, message: Message) -> None:
        try:
            message_id = message.message_id
            if not message.body:
                logger.warning(f"Empty message body for message ID: {message_id}")
                return  # For now, just skip empty messages
            message_body = json.loads(message.body.decode("utf-8"))
            logger.info(f"Processing message ID: {message_id}, tag: {message.tag}")

            match message.tag:
                case "CreateReview":
                    await self._handle_create_review(message_body)
                case "UpdateReview":
                    await self._handle_update_review(message_body)
                case "DeleteReview":
                    await self._handle_delete_review(message_body)
                case _:
                    logger.warning(f"Unknown message tag: {message.tag}")

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Invalid message format: {e}")

        except Exception as e:
            # Business logic errors
            logger.error(f"Error processing message: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown the consumer and background event loop."""
        self._running = False

        # Wait for consumer thread to finish first
        if hasattr(self, "_consumer_thread") and self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=self.SHUTDOWN_TIMEOUT_SECONDS)
            if self._consumer_thread.is_alive():
                logger.warning("Consumer thread did not finish in time")

        # Stop background event loop before closing consumer
        if hasattr(self, "loop") and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if hasattr(self, "loop_thread") and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5.0)
        if hasattr(self, "loop") and not self.loop.is_closed():
            self.loop.close()

        # Shutdown consumer after all async processing is complete
        if hasattr(self, "consumer"):
            self.consumer.shutdown()

        logger.info("RocketMQ consumer shutdown complete")

    def run_consumer(self) -> None:
        """Main loop running in a dedicated thread to receive and process messages."""
        logger.info("RocketMQ consumer start running")
        while self._running:
            try:
                messages = self.consumer.receive(
                    self.MAX_MESSAGE_NUM, self.INVISIBLE_DURATION
                )
                if messages and isinstance(messages, list):
                    # Process messages sequentially to maintain order
                    for message in messages:
                        if not self._running:
                            break  # Exit if shutdown initiated
                        try:
                            future = asyncio.run_coroutine_threadsafe(
                                self._consume(message), self.loop
                            )
                            future.result(timeout=self.MESSAGE_TIMEOUT_SECONDS)

                        except asyncio.TimeoutError as e:
                            logger.error(f"Message processing timed out: {e}")

                        except Exception as e:
                            logger.error(f"Message processing failed: {e}")

                        finally:
                            # Acknowledge message after processing
                            self.consumer.ack(message)

            except Exception as e:
                logger.error(f"Error in consumer looping: {e}")

        logger.info("RocketMQ consumer stopped")

    async def _handle_create_review(self, message_body: dict[str, Any]) -> None:
        review_id = message_body.get("ID")
        review_text = message_body.get("Text")
        target_id = message_body.get("TargetID")
        if review_id is None or review_text is None or target_id is None:
            logger.warning(f"CreateReview message missing fields: {message_body}")
            return
        embedding = await text_to_embedding(review_text)
        review_embedding = ReviewEmbedding(
            target_id=target_id,
            review_id=review_id,
            embedding=embedding,
            content=review_text,
        )
        await self.repository.save(review_embedding)

    async def _handle_update_review(self, message_body: dict[str, Any]) -> None:
        review_id = message_body.get("ID")
        review_text = message_body.get("Text")
        _ = message_body.get("TargetID")
        if review_id is None or review_text is None:
            logger.warning(f"UpdateReview message missing fields: {message_body}")
            return
        embedding = await text_to_embedding(review_text)
        await self.repository.update_embedding_review(
            review_id=review_id, embedding=embedding, review_content=review_text
        )

    async def _handle_delete_review(self, message_body: dict[str, Any]) -> None:
        review_id = message_body.get("ID")
        if review_id is not None:
            await self.repository.delete_by_id(document_id=review_id)
        else:
            logger.warning(f"DeleteReview message missing ID: {message_body}")
