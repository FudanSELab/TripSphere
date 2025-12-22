import asyncio
import json
import logging
import threading
from typing import Any

from pymongo import AsyncMongoClient
from rocketmq import (  # type: ignore
    ClientConfiguration,
    Credentials,
    FilterExpression,
    Message,
)
from rocketmq.v5.consumer import PushConsumer  # type: ignore
from rocketmq.v5.consumer.message_listener import (  # type: ignore
    ConsumeResult,
    MessageListener,
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


async def handle_create_review(msg_content: dict[str, Any]) -> None:
    review_id = msg_content.get("ID")
    review_text = msg_content.get("Text")
    attraction_id = msg_content.get("TargetID")
    embedding = await text_to_embedding_async(review_text)
    await repo.create_embedding(
        review_id=review_id,
        attraction_id=attraction_id,
        embedding=embedding,
        review_content=review_text,
    )


async def handle_update_review(msg_content: dict[str, Any]) -> None:
    review_id = msg_content.get("ID")
    review_text = msg_content.get("Text")
    _ = msg_content.get("TargetID")
    embedding = await text_to_embedding_async(review_text)
    await repo.update_embedding_by_review_id(
        review_id=review_id, embedding=embedding, review_content=review_text
    )


async def handle_delete_review(msg_content: dict[str, Any]) -> None:
    review_id = msg_content.get("ID")
    await repo.delete_embedding_by_review_id(review_id=review_id)


class ReviewMessageListener(MessageListener):
    def consume(self, message: Message) -> ConsumeResult:
        try:
            body_str = message.body.decode("utf-8")
            message_content = json.loads(body_str)
            message_tag = message.tag

            logger.info(
                f"Received message with tag: {message_tag}, ID: {message_content.get('ID')}"
            )

            # Obtain the background event loop and submit async tasks
            loop = get_or_create_event_loop()
            if message_tag == "CreateReview":
                future = asyncio.run_coroutine_threadsafe(
                    handle_create_review(message_content), loop
                )
            elif message_tag == "UpdateReview":
                future = asyncio.run_coroutine_threadsafe(
                    handle_update_review(message_content), loop
                )
            elif message_tag == "DeleteReview":
                future = asyncio.run_coroutine_threadsafe(
                    handle_delete_review(message_content), loop
                )
            else:
                logger.warning(f"Unknown tag: {message_tag}")
                return ConsumeResult.SUCCESS
            # Wait for the task to complete with a timeout
            future.result(timeout=30)
            return ConsumeResult.SUCCESS

        except Exception as e:
            logger.error(
                f"Error processing message (Tag: {message.tag}): {e}", exc_info=True
            )
            return ConsumeResult.FAILURE


def create_push_consumer() -> PushConsumer:
    consumer_group = "ReviewSummaryConsumerGroup"
    topic = "ReviewTopic"
    credentials = Credentials()
    config = ClientConfiguration(settings.rocketmq.namesrv_addr, credentials)
    consumer = PushConsumer(
        client_configuration=config,
        consumer_group=consumer_group,
        message_listener=ReviewMessageListener(),
        subscription={topic: FilterExpression()},
    )
    logger.info(f"Created consumer [{consumer_group}] for topic [{topic}]")
    return consumer
