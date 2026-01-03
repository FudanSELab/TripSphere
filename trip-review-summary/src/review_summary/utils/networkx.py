"""NetworkX utilities for Polars integration."""

from __future__ import annotations

from typing import Any, Iterable, cast

import networkx as nx
import polars as pl


def from_polars_edgelist(
    df: pl.DataFrame,
    source: str = "source",
    target: str = "target",
    edge_attr: str | list[str] | tuple[str, ...] | bool | None = None,
    create_using: type[nx.Graph[Any]] | nx.Graph[Any] | None = None,
    edge_key: str | None = None,
) -> nx.Graph[Any]:
    """Returns a graph from Polars DataFrame containing an edge list.

    The Polars DataFrame should contain at least two columns of node names and
    zero or more columns of edge attributes. Each row will be processed as one
    edge instance.

    Parameters
    ----------
    df : Polars DataFrame
        An edge list representation of a graph

    source : str
        A valid column name (string) for the source nodes (for the directed case).

    target : str
        A valid column name (string) for the target nodes (for the directed case).

    edge_attr : str or iterable of str, True, or None
        A valid column name (str) or iterable of column names that are
        used to retrieve items and add them to the graph as edge attributes.
        If `True`, all columns will be added except `source`, `target` and `edge_key`.
        If `None`, no edge attributes are added to the graph.

    create_using : NetworkX graph constructor, optional (default=nx.Graph)
        Graph type to create. If graph instance, then cleared before populated.

    edge_key : str or None, optional (default=None)
        A valid column name for the edge keys (for a MultiGraph). The values in
        this column are used for the edge keys when adding edges if create_using
        is a multigraph.

    Returns
    -------
    G : NetworkX graph
        A graph constructed from the edge list in the DataFrame.

    Examples
    --------
    >>> import polars as pl
    >>> import networkx as nx
    >>> edges = pl.DataFrame(
    ...     {
    ...         "source": [0, 1, 2],
    ...         "target": [2, 2, 3],
    ...         "weight": [3, 4, 5],
    ...         "color": ["red", "blue", "blue"],
    ...     }
    ... )
    >>> G = from_polars_edgelist(edges, edge_attr=True)
    >>> G[0][2]["color"]
    'red'

    Build multigraph with custom keys:

    >>> edges = pl.DataFrame(
    ...     {
    ...         "source": [0, 1, 2, 0],
    ...         "target": [2, 2, 3, 2],
    ...         "my_edge_key": ["A", "B", "C", "D"],
    ...         "weight": [3, 4, 5, 6],
    ...         "color": ["red", "blue", "blue", "blue"],
    ...     }
    ... )
    >>> G = from_polars_edgelist(
    ...     edges,
    ...     edge_key="my_edge_key",
    ...     edge_attr=["weight", "color"],
    ...     create_using=nx.MultiGraph(),
    ... )
    >>> G[0][2]
    AtlasView({'A': {'weight': 3, 'color': 'red'}, 'D': {'weight': 6, 'color': 'blue'}})
    """
    g: nx.Graph[Any] = cast(nx.Graph, nx.empty_graph(0, create_using))  # pyright: ignore

    if edge_attr is None:
        if g.is_multigraph() and edge_key is not None:
            assert isinstance(g, nx.MultiGraph)
            try:
                for u, v, k in zip(df[source], df[target], df[edge_key], strict=True):
                    g.add_edge(u, v, k)
            except (KeyError, pl.exceptions.ColumnNotFoundError) as err:
                msg = f"Invalid edge_key argument: {edge_key}"
                raise nx.NetworkXError(msg) from err
        else:
            g.add_edges_from(zip(df[source], df[target], strict=True))
        return g

    reserved_columns = [source, target]
    if g.is_multigraph() and edge_key is not None:
        reserved_columns.append(edge_key)

    # Additional columns requested
    attr_col_headings: Iterable[str | int] = []
    attribute_data: Iterable[Any] = []
    if edge_attr is True:
        attr_col_headings = [c for c in df.columns if c not in reserved_columns]
    elif isinstance(edge_attr, list | tuple):
        attr_col_headings = edge_attr
    else:
        attr_col_headings = [edge_attr]
    if len(attr_col_headings) == 0:
        raise nx.NetworkXError(
            "Invalid edge_attr argument: "
            f"No columns found with name: {attr_col_headings}"
        )

    try:
        attribute_data = zip(*[df[col] for col in attr_col_headings], strict=True)
    except (KeyError, TypeError, pl.exceptions.ColumnNotFoundError) as err:
        msg = f"Invalid edge_attr argument: {edge_attr}"
        raise nx.NetworkXError(msg) from err

    if g.is_multigraph():
        # => append the edge keys from the df to the bundled data
        if edge_key is not None:
            try:
                multigraph_edge_keys = df[edge_key]
                attribute_data = zip(attribute_data, multigraph_edge_keys, strict=True)
            except (KeyError, TypeError, pl.exceptions.ColumnNotFoundError) as err:
                msg = f"Invalid edge_key argument: {edge_key}"
                raise nx.NetworkXError(msg) from err

        for s, t, attrs in zip(df[source], df[target], attribute_data, strict=True):
            if edge_key is not None:
                attrs, multigraph_edge_key = attrs
                key = g.add_edge(s, t, key=multigraph_edge_key)
            else:
                key = g.add_edge(s, t)

            g[s][t][key].update(zip(attr_col_headings, attrs, strict=True))  # pyright: ignore
    else:
        for s, t, attrs in zip(df[source], df[target], attribute_data, strict=True):
            g.add_edge(s, t)
            g[s][t].update(zip(attr_col_headings, attrs, strict=True))  # pyright: ignore
    return g


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
    G : graph
        The NetworkX graph used to construct the Polars DataFrame.

    source : str, optional
        A valid column name (string) for the source nodes (for the directed case).

    target : str, optional
        A valid column name (string) for the target nodes (for the directed case).

    nodelist : list, optional
        Use only nodes specified in nodelist.

    edge_key : str or None, optional (default=None)
        A valid column name (string) for the edge keys (for the multigraph case).
        If None, edge keys are not stored in the DataFrame.

    Returns
    -------
    df : Polars DataFrame
       Graph edge list

    Examples
    --------
    >>> G = nx.Graph(
    ...     [
    ...         ("A", "B", {"cost": 1, "weight": 7}),
    ...         ("C", "E", {"cost": 9, "weight": 10}),
    ...     ]
    ... )
    >>> df = to_polars_edgelist(G, nodelist=["A", "C"])
    >>> df[["source", "target", "cost", "weight"]]
      source target  cost  weight
    0      A      B     1       7
    1      C      E     9      10

    >>> G = nx.MultiGraph([("A", "B", {"cost": 1}), ("A", "B", {"cost": 9})])
    >>> df = to_polars_edgelist(G, nodelist=["A", "C"], edge_key="ekey")
    >>> df[["source", "target", "cost", "ekey"]]
      source target  cost  ekey
    0      A      B     1     0
    1      A      B     9     1

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
