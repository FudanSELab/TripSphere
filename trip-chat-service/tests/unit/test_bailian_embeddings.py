from unittest.mock import patch

from mem0.embeddings.openai import OpenAIEmbedding

from chat.config.embeddings import EMBEDDING_BATCH_LIMIT, BailianOpenAIEmbedding


def test_embed_batch_splits_requests_at_bailian_limit() -> None:
    embedder = BailianOpenAIEmbedding.__new__(BailianOpenAIEmbedding)
    request_sizes: list[int] = []

    def embed_batch(texts: list[str], memory_action: str = "add") -> list[list[float]]:
        request_sizes.append(len(texts))
        return [[float(len(text))] for text in texts]

    with patch.object(OpenAIEmbedding, "embed_batch", side_effect=embed_batch):
        embeddings = embedder.embed_batch(
            [f"memory-{index}" for index in range(23)],
            "add",
        )

    assert request_sizes == [EMBEDDING_BATCH_LIMIT, EMBEDDING_BATCH_LIMIT, 3]
    assert len(embeddings) == 23
