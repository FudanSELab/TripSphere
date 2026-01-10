# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'SummarizationResult' model."""

from dataclasses import dataclass


@dataclass
class SummarizationResult:
    """Summarization result class definition."""

    id: str | tuple[str, str]
    description: str
