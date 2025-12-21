
import asyncio
import json
import logging
from typing import Dict, Any

from rocketmq import (ClientConfiguration, Credentials, FilterExpression,Message)
from rocketmq.v5.consumer import PushConsumer
from rocketmq.v5.consumer.message_listener import (ConsumeResult,MessageListener)

from review_summary.respositry.mongo import ReviewEmbeddingRepository
from review_summary.index.embedding import text_to_embedding_async
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "review_summary_db")
ROCK_MQ_NAMESRV_ADDR = os.getenv("ROCK_MQ_NAMESRV_ADDR", "47.120.37.103:8081")  # gRPC 地址
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
repo = ReviewEmbeddingRepository(db)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_create_review(msg_content: Dict[str, Any]):
    review_id = msg_content.get("ID")
    review_text = msg_content.get("Text")
    attraction_id = msg_content.get("TargetID")
    embedding = await text_to_embedding_async(review_text)
    await repo.create_embedding(
        review_id=review_id,
        attraction_id=attraction_id,
        embedding=embedding,
        review_content=review_text
    )

async def handle_update_review(msg_content: Dict[str, Any]):
    review_id = msg_content.get("ID")
    review_text = msg_content.get("Text")
    attraction_id = msg_content.get("TargetID")
    embedding = await text_to_embedding_async(review_text)
    await repo.update_embedding_by_review_id(
        review_id=review_id,
        embedding=embedding,
        review_content=review_text
    )

async def handle_delete_review(msg_content: Dict[str, Any]):
    review_id = msg_content.get("ID")
    await repo.delete_embedding_by_review_id(review_id=review_id)

class ReviewMessageListener(MessageListener):
    async def consume(self, message: Message) -> ConsumeResult:
        try:
            body_str = message.body.decode('utf-8')
            msg_content = json.loads(body_str)
            tag = message.tag

            logger.info(f"Received message with tag: {tag}, ID: {msg_content.get('ID')}")

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
            logger.error(f"Error processing message (Tag: {message.tag}): {e}", exc_info=True)
            return ConsumeResult.FAILURE

async def run_mq_consumer(stop_event: asyncio.Event):
    consumer_group = "ReviewSummaryConsumerGroup"
    topic = "ReviewTopic"
    credentials = Credentials()

    config = ClientConfiguration(ROCK_MQ_NAMESRV_ADDR, credentials)

    consumer = PushConsumer(
        config,
        consumer_group,
        ReviewMessageListener(),
        {topic: FilterExpression()}
    )

    logger.info(f"Starting consumer [{consumer_group}] for topic [{topic}]")
    try:
        consumer.startup()
        await stop_event.wait()
    finally:
        logger.info("Shutting down MQ consumer...")
        consumer.shutdown()
        logger.info("MQ consumer shut down")

# if __name__ == "__main__":
#     async def _main():
#         stop = asyncio.Event()
#         task = asyncio.create_task(run_mq_consumer(stop))
#         try:
#             await asyncio.sleep(3600)  # run for 1 hour or until Ctrl+C
#         except KeyboardInterrupt:
#             stop.set()
#         await task

#     asyncio.run(_main())