from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.seed_review_summary import EMBEDDING_BATCH_SIZE, embed_texts


class EmbedTextsTest(unittest.TestCase):
    def test_splits_requests_into_at_most_ten_texts(self) -> None:
        config = SimpleNamespace(
            embedding_base_url="http://example.test/v1",
            embedding_api_key="api-key",
            embedding_model="text-embedding-v4",
            embedding_dimensions=2,
            retries=0,
        )
        request_sizes: list[int] = []

        def post(*args: object, **kwargs: object) -> Mock:
            payload = kwargs["json"]
            inputs = payload["input"]
            request_sizes.append(len(inputs))
            response = Mock()
            response.json.return_value = {
                "data": [
                    {"index": index, "embedding": [float(index), 0.0]}
                    for index in range(len(inputs))
                ]
            }
            return response

        with patch("scripts.seed_review_summary.requests.post", side_effect=post):
            embeddings = embed_texts(
                config,  # type: ignore[arg-type]
                [f"text-{index}" for index in range(23)],
            )

        self.assertEqual([EMBEDDING_BATCH_SIZE, EMBEDDING_BATCH_SIZE, 3], request_sizes)
        self.assertEqual(23, len(embeddings))


if __name__ == "__main__":
    unittest.main()
