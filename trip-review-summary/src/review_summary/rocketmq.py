import asyncio
import json
import logging
import threading
from typing import Any, cast

from pymongo import AsyncMongoClient
from rocketmq import (  # type: ignore
    ClientConfiguration,
    Credentials,
    FilterExpression,
    Message,
)
from rocketmq.v5.consumer import SimpleConsumer  # type: ignore
from rocketmq.v5.consumer.message_listener import (  # type: ignore
    ConsumeResult,
)

from review_summary.config.settings import get_settings
from review_summary.index.embedding import text_to_embedding_async
from review_summary.index.repository import ReviewEmbeddingRepository

logger = logging.getLogger(__name__)

settings = get_settings()
client = AsyncMongoClient[dict[str, Any]](settings.mongo.uri)
db = client[settings.mongo.database]
repo = ReviewEmbeddingRepository(db[ReviewEmbeddingRepository.COLLECTION_NAME])


# Dedicated background event loop for running async message handlers
_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None


def _start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Run the given event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Get or create the event loop used for message processing.

    This function ensures we have a single long-running event loop
    running in a dedicated daemon thread so coroutines can be submitted from
    synchronous callbacks using `asyncio.run_coroutine_threadsafe`.
    """
    global _loop, _loop_thread
    if _loop is None or not _loop.is_running():
        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(
            target=_start_background_loop, args=(_loop,), daemon=True
        )
        _loop_thread.start()
    return _loop


async def handle_create_review(msg_body: dict[str, Any]) -> None:
    review_id = msg_body.get("ID")
    review_text = msg_body.get("Text")
    attraction_id = msg_body.get("TargetID")
    if review_id is None or review_text is None or attraction_id is None:
        logger.warning(f"CreateReview message missing fields: {msg_body}")
        return
    embedding = await text_to_embedding_async(review_text)
    await repo.create_embedding(
        review_id=review_id,
        attraction_id=attraction_id,
        embedding=embedding,
        review_content=review_text,
    )


async def handle_update_review(msg_body: dict[str, Any]) -> None:
    review_id = msg_body.get("ID")
    review_text = msg_body.get("Text")
    _ = msg_body.get("TargetID")
    if review_id is None or review_text is None:
        logger.warning(f"UpdateReview message missing fields: {msg_body}")
        return
    embedding = await text_to_embedding_async(review_text)
    await repo.update_embedding_by_review_id(
        review_id=review_id, embedding=embedding, review_content=review_text
    )


async def handle_delete_review(msg_body: dict[str, Any]) -> None:
    review_id = msg_body.get("ID")
    if review_id is not None:
        await repo.delete_embedding_by_review_id(review_id=review_id)
    else:
        logger.warning(f"DeleteReview message missing ID: {msg_body}")


def consume(message: Message) -> ConsumeResult:
    try:
        message_body = cast(bytes | None, message.body)  # pyright: ignore[reportUnknownMemberType]
        if message_body is None:
            logger.warning("Received message with empty body")
            return ConsumeResult.SUCCESS
        body_str = message_body.decode("utf-8")
        msg_body = json.loads(body_str)
        msg_tag = cast(str, message.tag)  # pyright: ignore[reportUnknownMemberType]

        logger.info(f"Received message with tag: {msg_tag}, ID: {msg_body.get('ID')}")

        # Obtain the background event loop and submit async tasks
        loop = get_or_create_event_loop()
        if msg_tag == "CreateReview":
            future = asyncio.run_coroutine_threadsafe(
                handle_create_review(msg_body), loop
            )
        elif msg_tag == "UpdateReview":
            future = asyncio.run_coroutine_threadsafe(
                handle_update_review(msg_body), loop
            )
        elif msg_tag == "DeleteReview":
            future = asyncio.run_coroutine_threadsafe(
                handle_delete_review(msg_body), loop
            )
        else:
            logger.warning(f"Unknown tag: {msg_tag}")
            return ConsumeResult.SUCCESS
        # Wait for the task to complete with a timeout
        future.result(timeout=30)
        return ConsumeResult.SUCCESS

    except Exception as e:
        msg_tag = cast(str, message.tag)  # pyright: ignore[reportUnknownMemberType]
        logger.error(f"Error processing message (Tag {msg_tag}): {e}")
        return ConsumeResult.FAILURE


def create_simple_consumer() -> SimpleConsumer:
    consumer_group = "ReviewSummaryConsumerGroup"
    topic = "ReviewTopic"
    credentials = Credentials()
    config = ClientConfiguration(settings.rocketmq.namesrv_addr, credentials)
    consumer = SimpleConsumer(
        client_configuration=config,
        consumer_group=consumer_group,
        subscription={topic: FilterExpression()},
    )
    logger.info(f"Created consumer [{consumer_group}] for topic [{topic}]")
    return consumer


def run_simple_consumer(consumer: SimpleConsumer, stop_event: threading.Event) -> None:
    consumer.startup()
    logger.info("SimpleConsumer started and ready to receive messages.")
    try:
        while not stop_event.is_set():
            try:
                messages = consumer.receive(32, 15)  # type: ignore
                if messages is not None:  # type: ignore
                    for msg in messages:  # type: ignore
                        result = consume(msg)  # type: ignore
                        if result == ConsumeResult.SUCCESS:
                            consumer.ack(msg)  # type: ignore
                        else:
                            # Do not acknowledge failed messages to allow retry or other handling
                            logger.error("Message processing failed; skipping ACK.")
            except Exception as e:
                if not stop_event.is_set():
                    logger.error(f"Error receiving messages: {e}")
    except Exception as e:
        if not stop_event.is_set():
            logger.error(f"Error in consumer loop: {e}")
    finally:
        logger.info("Shutting down SimpleConsumer...")
        consumer.shutdown()
