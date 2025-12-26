from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

from review_summary.index.repository import ReviewEmbedding, ReviewEmbeddingRepository


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
    ) -> list[ReviewEmbedding]:
        raise NotImplementedError
