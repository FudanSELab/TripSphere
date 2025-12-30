# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import asyncio
from typing import Any

import numpy as np
from langchain_openai.embeddings import OpenAIEmbeddings

from review_summary.config.settings import get_settings
from review_summary.index.text_splitting import TokenTextSplitter
from review_summary.tokenizer.tiktoken import TiktokenTokenizer


async def embed_text(
    texts: list[str],
    batch_size: int = 16,
    batch_max_tokens: int = 8191,
    num_threads: int = 4,
    model_config: dict[str, Any] | None = None,
) -> list[list[float] | None]:
    model_config = model_config or {}
    splitter = TokenTextSplitter(
        TiktokenTokenizer(model_config.get("encoding_name", "cl100k_base")),
        chunk_size=batch_max_tokens,
    )
    openai_settings = get_settings().openai
    model = OpenAIEmbeddings(
        model=model_config.get("model_name", "text-embedding-3-large"),
        api_key=openai_settings.api_key,
        base_url=openai_settings.base_url,
    )
    semaphore = asyncio.Semaphore(num_threads)
    # Break up the input texts. The sizes here indicate
    # how many snippets are in each input text
    texts, input_sizes = _prepare_embed_texts(texts, splitter)
    text_batches = _create_text_batches(texts, batch_size, batch_max_tokens, splitter)

    # Embed each chunk of snippets
    embeddings = await _execute(model, text_batches, semaphore)
    return _reconstitute_embeddings(embeddings, input_sizes)


async def _execute(
    model: OpenAIEmbeddings, chunks: list[list[str]], semaphore: asyncio.Semaphore
) -> list[list[float]]:
    async def embed(chunk: list[str]) -> np.ndarray:
        async with semaphore:
            chunk_embeddings = await model.aembed_documents(chunk)
        return np.array(chunk_embeddings)

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
    texts: list[str], splitter: TokenTextSplitter
) -> tuple[list[str], list[int]]:
    sizes: list[int] = []
    snippets: list[str] = []

    for text in texts:
        # Split the input text and filter out any empty content
        split_texts = splitter.split_text(text)
        if len(split_texts) == 0:
            continue
        split_texts = [txt for txt in split_texts if len(txt) > 0]

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
