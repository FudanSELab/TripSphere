from unittest.mock import patch

import pytest

from review_summary.index.operations.embed_text import embed_text


class _FakeEmbeddings:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.model = kwargs.get("model", "text-embedding-v4")
        self.batches: list[list[str]] = []

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        self.batches.append(list(texts))
        return [[float(len(text))] for text in texts]


@pytest.mark.asyncio
async def test_embed_text_limits_each_request_to_ten_strings() -> None:
    fake = _FakeEmbeddings()

    def create_embeddings(**kwargs: object) -> _FakeEmbeddings:
        fake.kwargs = kwargs
        return fake

    with patch(
        "review_summary.index.operations.embed_text.OpenAIEmbeddings",
        side_effect=create_embeddings,
    ):
        embeddings = await embed_text(
            [f"text-{index}" for index in range(23)],
            {"model": "text-embedding-v4"},
            batch_size=16,
        )

    assert [len(batch) for batch in fake.batches] == [10, 10, 3]
    assert fake.kwargs["check_embedding_ctx_length"] is False
    assert len(embeddings) == 23
