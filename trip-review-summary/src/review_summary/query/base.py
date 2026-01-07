"""Base classes for search algos."""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class SearchResult:
    """A Structured Search Result."""

    response: str | dict[str, Any] | list[dict[str, Any]]
    context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    # actual text strings that are in the context window, built from context_data
    context_text: str | list[str] | dict[str, str]
    completion_time: float
    # total LLM calls and token usage
    llm_calls: int
    prompt_tokens: int
    output_tokens: int
    # breakdown of LLM calls and token usage
    llm_calls_categories: dict[str, int] | None = None
    prompt_tokens_categories: dict[str, int] | None = None
    output_tokens_categories: dict[str, int] | None = None
