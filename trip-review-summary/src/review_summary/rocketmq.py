import json
import logging
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
            msg_content = json.loads(body_str)
            tag = message.tag

            logger.info(
                f"Received message with tag: {tag}, ID: {msg_content.get('ID')}"
            )

            if tag == "CreateReview":
                await handle_create_review(msg_content)
            elif tag == "UpdateReview":
                await handle_update_review(msg_content)
            elif tag == "DeleteReview":
                await handle_delete_review(msg_content)
            else:
                logger.warning(f"Unknown tag: {tag}")

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
