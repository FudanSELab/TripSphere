import asyncio
import json
import logging
import threading
from asyncio import AbstractEventLoop
from typing import Any

from rocketmq import (  # pyright: ignore[reportMissingTypeStubs]
    ClientConfiguration,
    Credentials,
    FilterExpression,
    Message,
    SimpleConsumer,
)

from review_summary.config.settings import get_settings
from review_summary.index.embedding import text_to_embedding
from review_summary.index.repository import ReviewEmbedding, ReviewEmbeddingRepository

logger = logging.getLogger(__name__)


class RocketMQConsumer:
    CONSUMER_GROUP = "ReviewSummaryConsumerGroup"
    TOPIC = "ReviewTopic"
    MAX_MESSAGE_NUM = 32
    INVISIBLE_DURATION = 10
    WAIT_TIMEOUT_SECONDS = 32

    def __init__(self, repository: ReviewEmbeddingRepository) -> None:
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

        # Initialize background event loop for async processing
        def _start_event_loop(loop: AbstractEventLoop) -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(
            target=_start_event_loop, args=(self.loop,), daemon=True
        )
        self.loop_thread.start()

        self.repository = repository

        # Start consumer in a separate thread
        self._running = True
        self._run_consumer_task = asyncio.create_task(
            asyncio.to_thread(self.run_consumer)
        )

    async def _consume(self, message: Message) -> None:
        try:
            message_tag = message.tag if message.tag else "unknown"
            message_id = message.message_id if message.message_id else "unknown"
            message_body = json.loads(message.body.decode("utf-8"))
            logger.info(f"Processing message ID: {message_id}, tag: {message_tag}")

            match message_tag:
                case "CreateReview":
                    await self.handle_create_review(message_body)
                case "UpdateReview":
                    await self.handle_update_review(message_body)
                case "DeleteReview":
                    await self.handle_delete_review(message_body)
                case _:
                    logger.warning(f"Unknown message tag: {message_tag}")

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Invalid message format: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

        self.consumer.ack(message)  # Acknowledge message after processing

    async def shutdown(self) -> None:
        self._running = False
        # Wait for consumer task to finish
        if self._run_consumer_task:
            try:
                await asyncio.wait_for(self._run_consumer_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Consumer task did not finish in time")
        self.consumer.shutdown()
        # Stop background event loop
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join(timeout=5.0)
        if not self.loop.is_closed():
            self.loop.close()

    def run_consumer(self) -> None:
        logger.info("RocketMQ consumer start running")
        app_settings = get_settings().app
        while self._running:
            try:
                messages = self.consumer.receive(
                    self.MAX_MESSAGE_NUM, self.INVISIBLE_DURATION
                )
                if messages is not None and len(messages) > 0:
                    # Process messages sequentially to maintain order
                    for message in messages:
                        try:
                            future = asyncio.run_coroutine_threadsafe(
                                self._consume(message), self.loop
                            )
                            future.result(timeout=self.WAIT_TIMEOUT_SECONDS)
                        except Exception as e:
                            logger.error(f"Message processing failed: {e}")
                            # Ack on error to prevent blocking the queue
                            self.consumer.ack(message)
            except Exception as e:
                logger.error(
                    f"Error in consumer loop: {e}", exc_info=app_settings.debug
                )
        logger.info("RocketMQ consumer stopped")

    async def handle_create_review(self, message_body: dict[str, Any]) -> None:
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

    async def handle_update_review(self, message_body: dict[str, Any]) -> None:
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

    async def handle_delete_review(self, message_body: dict[str, Any]) -> None:
        review_id = message_body.get("ID")
        if review_id is not None:
            await self.repository.delete_by_id(document_id=review_id)
        else:
            logger.warning(f"DeleteReview message missing ID: {message_body}")
