from __future__ import annotations

import networkx as nx
import polars as pl


def compute_degree(graph: nx.Graph[str]) -> pl.DataFrame:
    """Create a new DataFrame with the degree of each node in the graph."""
    return pl.DataFrame(
        [{"title": node, "degree": degree} for node, degree in graph.degree()]
    )
