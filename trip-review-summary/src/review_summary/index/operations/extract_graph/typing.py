# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Unit' and 'ExtractionResult' models."""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import pandas as pd


@dataclass
class Unit:
    """Unit class definition."""

    id: str
    text: str


@dataclass
class ExtractionResult:
    """Extraction result class definition."""

    entities: pd.DataFrame
    relationships: pd.DataFrame
    graph: nx.Graph[str] | None
