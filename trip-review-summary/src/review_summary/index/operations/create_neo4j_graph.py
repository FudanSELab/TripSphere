from __future__ import annotations

import polars as pl


def create_neo4j_graph(
    edges: pl.DataFrame,
    edge_attr: list[str] | None = None,
    nodes: pl.DataFrame | None = None,
    node_id: str = "title",
) -> None:
    """Create a neo4j graph from nodes and edges dataframes."""
    raise NotImplementedError
