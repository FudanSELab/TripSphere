from typing import Any

import tiktoken

from review_summary.index.operations.chunk_text.typing import TextChunk
from review_summary.index.text_splitting import (
    DecodeFn,
    EncodeFn,
    TokenChunkerOptions,
    split_multiple_texts_on_tokens,
)


def get_encoding_fn(encoding_name: str) -> tuple[EncodeFn, DecodeFn]:
    """Get the encoding model."""
    enc = tiktoken.get_encoding(encoding_name)

    def encode(text: str) -> list[int]:
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

    return encode, decode


def chunk_text(
    texts: list[str], config: dict[str, Any] | None = None
) -> list[TextChunk]:
    """Chunks text into chunks based on encoding tokens."""
    config = config or {}
    tokens_per_chunk = config.get("size", 1200)
    chunk_overlap = config.get("overlap", 100)
    encoding_name = config.get("encoding_model", "cl100k_base")

    encode, decode = get_encoding_fn(encoding_name)
    return split_multiple_texts_on_tokens(
        texts,
        TokenChunkerOptions(
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=tokens_per_chunk,
            encode=encode,
            decode=decode,
        ),
    )
