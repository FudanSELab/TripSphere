# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
from typing import Any

import numpy as np

from review_summary.index.text_splitting import TokenTextSplitter
from review_summary.tokenizer.factory import get_tokenizer


async def embed_text(
    texts: list[str], config: dict[str, Any] | None = None
) -> list[list[float]]:
    config = config or {}
    batch_size = config.get("batch_size", 16)
    batch_max_tokens = config.get("batch_max_tokens", 8191)
    llm_config = config.get("llm", {})
    splitter = _get_splitter(llm_config, batch_max_tokens)
    semaphore = asyncio.Semaphore(config.get("num_threads", 4))

    # Break up the input texts. The sizes here indicate
    # how many snippets are in each input text
    texts, input_sizes = _prepare_embed_texts(texts, splitter)
    text_batches = _create_text_batches(
        texts,
        batch_size,
        batch_max_tokens,
        splitter,
    )


def _get_splitter(config: dict[str, Any], batch_max_tokens: int) -> TokenTextSplitter:
    return TokenTextSplitter(
        tokenizer=get_tokenizer(model_config=config),
        chunk_size=batch_max_tokens,
    )


async def _execute(
    model: EmbeddingModel, chunks: list[list[str]], semaphore: asyncio.Semaphore
) -> list[list[float]]:
    async def embed(chunk: list[str]) -> np.ndarray:
        async with semaphore:
            chunk_embeddings = await model.aembed_batch(chunk)
            result = np.array(chunk_embeddings)
        return result

    futures = [embed(chunk) for chunk in chunks]
    results = await asyncio.gather(*futures)
    # merge results in a single list of lists (reduce the collect dimension)
    return [item for sublist in results for item in sublist]


def _create_text_batches(
    texts: list[str],
    max_batch_size: int,
    max_batch_tokens: int,
    splitter: TokenTextSplitter,
) -> list[list[str]]:
    """Create batches of texts to embed."""
    # https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
    # According to this embeddings reference, Azure limits us to
    # 16 concurrent embeddings and 8191 tokens per request
    result: list[list[str]] = []
    current_batch: list[str] = []
    current_batch_tokens = 0

    for text in texts:
        token_count = splitter.num_tokens(text)
        if (
            len(current_batch) >= max_batch_size
            or current_batch_tokens + token_count > max_batch_tokens
        ):
            result.append(current_batch)
            current_batch = []
            current_batch_tokens = 0

        current_batch.append(text)
        current_batch_tokens += token_count

    if len(current_batch) > 0:
        result.append(current_batch)

    return result


def _prepare_embed_texts(
    input: list[str], splitter: TokenTextSplitter
) -> tuple[list[str], list[int]]:
    sizes: list[int] = []
    snippets: list[str] = []

    for text in input:
        # Split the input text and filter out any empty content
        split_texts = splitter.split_text(text)
        if len(split_texts) == 0:
            continue
        split_texts = [text for text in split_texts if len(text) > 0]

        sizes.append(len(split_texts))
        snippets.extend(split_texts)

    return snippets, sizes


def _reconstitute_embeddings(
    raw_embeddings: list[list[float]], sizes: list[int]
) -> list[list[float] | None]:
    """Reconstitute the embeddings into the original input texts."""
    embeddings: list[list[float] | None] = []
    cursor = 0
    for size in sizes:
        if size == 0:
            embeddings.append(None)
        elif size == 1:
            embedding = raw_embeddings[cursor]
            embeddings.append(embedding)
            cursor += 1
        else:
            chunk = raw_embeddings[cursor : cursor + size]
            average = np.average(chunk, axis=0)
            normalized = average / np.linalg.norm(average)
            embeddings.append(normalized.tolist())
            cursor += size
    return embeddings
