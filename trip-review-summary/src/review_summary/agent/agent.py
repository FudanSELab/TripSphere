import os

from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

from review_summary.index.repository import ReviewEmbedding, ReviewEmbeddingRepository

# Load environment variables
ATTRACTION_GRPC_SERVICE_HOST = os.getenv("ATTRACTION_GRPC_SERVICE_HOST", "127.0.0.1")
ATTRACTION_GRPC_SERVICE_PORT = int(os.getenv("ATTRACTION_GRPC_SERVICE_PORT", "9007"))


class ReviewSummaryAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(
        self,
        chat_model: ChatOpenAI,
        embedding_model: OpenAIEmbeddings,
        repository: ReviewEmbeddingRepository,
    ):
        self.model = chat_model
        self.embedding_model = embedding_model
        self.repository = repository

    async def retrieve_reviews(
        self, target_id: str, query: str, top_k: int = 20
    ) -> list[ReviewEmbedding]: ...
