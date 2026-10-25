from typing import Literal

from mem0.embeddings.openai import OpenAIEmbedding

# text-embedding-v4 accepts at most 10 strings per request.
EMBEDDING_BATCH_LIMIT = 10


class BailianOpenAIEmbedding(OpenAIEmbedding):
    """OpenAI-compatible embedder constrained to Bailian's batch limit."""

    def embed_batch(
        self,
        texts: list[str],
        memory_action: Literal["add", "search", "update"] = "add",
    ) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_LIMIT):
            batch = texts[start : start + EMBEDDING_BATCH_LIMIT]
            embeddings.extend(super().embed_batch(batch, memory_action))
        return embeddings
