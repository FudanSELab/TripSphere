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
    texts: list[str],
    tokens_per_chunk: int = 1200,
    chunk_overlap: int = 100,
    encoding_name: str = "cl100k_base",
) -> list[TextChunk]:
    """Chunks text into chunks based on encoding tokens."""
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
