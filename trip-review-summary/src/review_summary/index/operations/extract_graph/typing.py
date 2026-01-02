# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Unit' and 'ExtractionResult' models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx
import polars as pl


@dataclass
class Unit:
    """Unit class definition."""

    id: str
    text: str


@dataclass
class ExtractionResult:
    """Extraction result class definition."""

    entities: pl.LazyFrame
    relationships: pl.LazyFrame
    graph: nx.Graph[Any] | None
