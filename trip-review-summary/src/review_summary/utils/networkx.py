"""NetworkX utilities for Polars integration."""

from __future__ import annotations

from typing import Any

import networkx as nx
import polars as pl


def to_polars_edgelist(
    G: nx.Graph[Any],
    source: str = "source",
    target: str = "target",
    nodelist: list[Any] | None = None,
    edge_key: str | None = None,
) -> pl.DataFrame:
    """Returns the graph edge list as a Polars DataFrame.

    Parameters
    ----------
    G : NetworkX graph
        The NetworkX graph used to construct the Polars DataFrame.

    source : str, optional
        Column name for source nodes (default: "source").

    target : str, optional
        Column name for target nodes (default: "target").

    nodelist : list[Any], optional
        Use only nodes specified in nodelist.

    edge_key : str or None, optional
        Column name for edge keys in multigraphs (default: None).
        If None, edge keys are not stored in the DataFrame.

    Returns
    -------
    df : Polars DataFrame
        Graph edge list with all edge attributes as columns.

    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.Graph([("A", "B", {"weight": 7, "cost": 1})])
    >>> df = to_polars_edgelist(G)
    >>> df
    shape: (1, 4)
    ┌────────┬────────┬────────┬──────┐
    │ source │ target │ weight │ cost │
    │ ---    │ ---    │ ---    │ ---  │
    │ str    │ str    │ i64    │ i64  │
    ╞════════╪════════╪════════╪══════╡
    │ A      │ B      │ 7      │ 1    │
    └────────┴────────┴────────┴──────┘
    """
    if nodelist is None:
        edgelist = G.edges(data=True)
    else:
        edgelist = G.edges(nodelist, data=True)
    source_nodes = [s for s, _, _ in edgelist]
    target_nodes = [t for _, t, _ in edgelist]

    all_attrs = set[str]().union(*(d.keys() for _, _, d in edgelist))
    if source in all_attrs:
        raise nx.NetworkXError(f"Source name {source!r} is an edge attr name")
    if target in all_attrs:
        raise nx.NetworkXError(f"Target name {target!r} is an edge attr name")

    # Use None instead of nan for missing values (Polars handles None natively)
    edge_attr = {k: [d.get(k, None) for _, _, d in edgelist] for k in all_attrs}

    if G.is_multigraph() and edge_key is not None:
        assert isinstance(G, nx.MultiGraph)
        if edge_key in all_attrs:
            raise nx.NetworkXError(f"Edge key name {edge_key!r} is an edge attr name")
        edge_keys = [k for _, _, k in G.edges(keys=True)]
        edgelistdict = {source: source_nodes, target: target_nodes, edge_key: edge_keys}
    else:
        edgelistdict = {source: source_nodes, target: target_nodes}

    edgelistdict.update(edge_attr)
    return pl.DataFrame(edgelistdict)
