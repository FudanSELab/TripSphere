import asyncio
import json
import logging
import threading
from asyncio import AbstractEventLoop
from typing import Any, cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct
from rocketmq import (  # type: ignore
    ClientConfiguration,
    Credentials,
    FilterExpression,
    SimpleConsumer,
)  # pyright: ignore[reportMissingTypeStubs]
from rocketmq import (  # pyright: ignore[reportMissingTypeStubs]
    Message as RocketmqMessage,
)

from review_summary.config.settings import get_settings
from review_summary.index.operations.chunk_text.chunk_text import chunk_text
from review_summary.index.operations.embed_text import embed_text
from review_summary.models import TextUnit
from review_summary.rocketmq.typing import CreateReview, Message
from review_summary.utils.hashing import gen_sha512_hash
from review_summary.vector_stores.reviews import ReviewVectorStore

logger = logging.getLogger(__name__)


class RocketMQConsumer:
    CONSUMER_GROUP = "ReviewSummaryConsumerGroup"
    TOPIC = "ReviewTopic"
    MAX_MESSAGE_NUM = 16
    INVISIBLE_DURATION = 15
    MESSAGE_TIMEOUT_SECONDS = 10
    # MESSAGE_TIMEOUT + buffer for graceful shutdown
    SHUTDOWN_TIMEOUT_SECONDS = 15

    def __init__(self, qdrant_client: AsyncQdrantClient) -> None:
        # Store singleton Qdrant client for message processing
        self.qdrant_client = qdrant_client
        self.vector_store = ReviewVectorStore(client=qdrant_client)

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
        self.running = True
        self.consumer_thread = threading.Thread(target=self._run_consumer, daemon=True)
        self.consumer_thread.start()

    async def _consume(self, message: Message) -> None:
        try:
            message_id = message.message_id
            if message.body is None:
                logger.warning(f"Empty message body for message ID: {message_id}")
                return  # For now, just skip empty messages
            message_body = cast(
                dict[str, Any], json.loads(message.body.decode("utf-8"))
            )
            logger.info(f"Process message ID: {message_id}, tag: {message.tag}")

            match message.tag:
                case "CreateReview":
                    await self._handle_create_review(message_body)
                case "UpdateReview":
                    await self._handle_update_review(message_body)
                case "DeleteReview":
                    await self._handle_delete_review(message_body)
                case _:
                    logger.warning(f"Unknown message tag: {message.tag}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown the consumer and background event loop."""
        self.running = False

        # Wait for consumer thread to finish first
        if hasattr(self, "consumer_thread") and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=self.SHUTDOWN_TIMEOUT_SECONDS)
            if self.consumer_thread.is_alive():
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

    def _run_consumer(self) -> None:
        """Main loop running in a dedicated thread to receive messages."""
        logger.info("RocketMQ consumer start running")
        while self.running is True:
            try:
                rmq_messages = cast(
                    list[RocketmqMessage],
                    self.consumer.receive(  # pyright: ignore[reportUnknownMemberType]
                        self.MAX_MESSAGE_NUM, self.INVISIBLE_DURATION
                    ),
                )
                if len(rmq_messages) == 0:
                    continue
                # Process messages sequentially to maintain order
                for rmq_message in rmq_messages:
                    if not self.running:
                        break  # Exit if shutdown initiated
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._consume(Message.from_rmq_message(rmq_message)),
                            self.loop,
                        )
                        future.result(timeout=self.MESSAGE_TIMEOUT_SECONDS)

                    except Exception as e:
                        logger.error(f"Message processing error: {e}")

                    finally:
                        # Acknowledge message after processing
                        self.consumer.ack(rmq_message)

            except Exception as e:
                logger.error(f"Error in receiving messages: {e}")

        logger.info("RocketMQ consumer stopped")

    async def _handle_create_review(self, message_body: dict[str, Any]) -> None:
        """Handle the CreateReview event."""
        create_review = CreateReview.model_validate(message_body, by_alias=True)

        # Create basic text units
        text_chunks = chunk_text([create_review.text])
        text_units: list[TextUnit] = []
        for idx, text_chunk in enumerate(text_chunks):
            text_unit_id = gen_sha512_hash({"chunk": text_chunk.text_chunk}, ["chunk"])
            short_id = f"/reviews/{create_review.id}/text-units/{idx}"
            text_unit = TextUnit(
                id=text_unit_id,
                short_id=short_id,
                text=text_chunk.text_chunk,
                n_tokens=text_chunk.n_tokens,
                document_id=create_review.id,
                attributes={"target_id": create_review.target_id},
            )
            text_units.append(text_unit)

        # Generate text embeddings
        embeddings = await embed_text(
            texts=[text_unit.text for text_unit in text_units],
            model_config={
                "model_name": "text-embedding-3-large",
                "encoding_name": "cl100k_base",
            },
        )

        # Save to vector store
        points: list[PointStruct] = []
        for text_unit, embedding in zip(text_units, embeddings, strict=True):
            if embedding is None:
                logger.warning(
                    f"Skipping text unit {text_unit.short_id} due to empty embedding"
                )
                continue
            payload = text_unit.model_dump()
            text_unit_id = payload.pop("id")
            point = PointStruct(id=text_unit_id, vector=embedding, payload=payload)
            points.append(point)
        await self.vector_store.save(points)

    async def _handle_delete_review(self, message_body: dict[str, Any]) -> None:
        """Handle the DeleteReview event."""

    async def _handle_update_review(self, message_body: dict[str, Any]) -> None:
        """Handle the UpdateReview event."""
