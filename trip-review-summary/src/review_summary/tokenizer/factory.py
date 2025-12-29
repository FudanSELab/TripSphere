# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Get Tokenizer."""

from typing import Any, cast

from review_summary.tokenizer.litellm import LitellmTokenizer
from review_summary.tokenizer.tiktoken import TiktokenTokenizer
from review_summary.tokenizer.tokenizer import Tokenizer


def get_tokenizer(
    model_config: dict[str, Any] | None = None,
    encoding_model: str = "cl100k_base",
) -> Tokenizer:
    """Get the tokenizer for the given model configuration
    or fallback to a tiktoken based tokenizer.

    Arguments:
        model_config: The model configuration.
            If not provided or model_config.encoding_model is manually set,
            use a tiktoken based tokenizer. Otherwise, use a LitellmTokenizer
            based on the model name. LiteLLM supports token encoding/decoding
            for the range of models it supports.
        encoding_model: A tiktoken encoding model to use
            if no model configuration is provided. Only used if a model configuration
            is not provided.

    Returns:
        An instance of a Tokenizer.
    """
    if model_config is not None:
        _encoding_model = cast(str, model_config.get("encoding_model", ""))
        if _encoding_model.strip() != "":
            # User has manually specified a tiktoken encoding model
            # to use for the provided model configuration.
            return TiktokenTokenizer(encoding_name=_encoding_model)

        return LitellmTokenizer(model_name=model_config.get("model", ""))

    return TiktokenTokenizer(encoding_name=encoding_model)
