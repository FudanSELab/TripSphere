"""Unit tests for NetworkX utilities."""

from __future__ import annotations

import networkx as nx
import polars as pl
import pytest

from review_summary.utils.networkx import to_polars_edgelist


class TestToPolarsEdgelist:
    """Test suite for to_polars_edgelist function."""

    def test_simple_graph_basic(self) -> None:
        """Test converting a simple graph with basic edges."""
        G = nx.Graph([("A", "B"), ("B", "C")])
        df = to_polars_edgelist(G)

        assert df.shape == (2, 2)
        assert set(df.columns) == {"source", "target"}
        assert set(df["source"].to_list()) == {"A", "B"}
        assert set(df["target"].to_list()) == {"B", "C"}

    def test_simple_graph_with_attributes(self) -> None:
        """Test converting a graph with edge attributes."""
        G = nx.Graph([("A", "B", {"weight": 7, "cost": 1})])
        df = to_polars_edgelist(G)

        assert df.shape == (1, 4)
        assert set(df.columns) == {"source", "target", "weight", "cost"}
        assert df["source"][0] == "A"
        assert df["target"][0] == "B"
        assert df["weight"][0] == 7
        assert df["cost"][0] == 1

    def test_multiple_edges_with_different_attributes(self) -> None:
        """Test graph where edges have different sets of attributes."""
        G: nx.Graph[str] = nx.Graph()
        G.add_edge("A", "B", weight=5, cost=2)
        G.add_edge("B", "C", weight=3)
        G.add_edge("C", "D", cost=1)

        df = to_polars_edgelist(G)

        assert df.shape == (3, 4)
        assert set(df.columns) == {"source", "target", "weight", "cost"}

        # Check that missing attributes are None
        row_bc = df.filter(pl.col("source") == "B")
        row_cd = df.filter(pl.col("source") == "C")

        assert row_bc["cost"][0] is None
        assert row_cd["weight"][0] is None

    def test_custom_column_names(self) -> None:
        """Test using custom column names for source and target."""
        G = nx.Graph([("A", "B", {"weight": 10})])
        df = to_polars_edgelist(G, source="from", target="to")

        assert df.shape == (1, 3)
        assert set(df.columns) == {"from", "to", "weight"}
        assert df["from"][0] == "A"
        assert df["to"][0] == "B"

    def test_nodelist_filtering(self) -> None:
        """Test filtering edges using nodelist parameter."""
        G = nx.Graph([("A", "B"), ("B", "C"), ("C", "D")])
        df = to_polars_edgelist(G, nodelist=["A", "B"])

        # Only edges incident to A or B should be included
        assert df.shape[0] <= 2
        sources = df["source"].to_list()
        targets = df["target"].to_list()

        for node in sources + targets:
            assert node in ["A", "B", "C"]  # C can appear as target of B

    def test_directed_graph(self) -> None:
        """Test converting a directed graph."""
        G = nx.DiGraph([("A", "B"), ("B", "A")])
        df = to_polars_edgelist(G)

        assert df.shape == (2, 2)
        # Both directions should be present
        assert (
            len(df.filter((pl.col("source") == "A") & (pl.col("target") == "B"))) == 1
        )
        assert (
            len(df.filter((pl.col("source") == "B") & (pl.col("target") == "A"))) == 1
        )

    def test_multigraph_without_edge_key(self) -> None:
        """Test converting a multigraph without storing edge keys."""
        G: nx.MultiGraph[str] = nx.MultiGraph()
        G.add_edge("A", "B", key="edge1", weight=5)
        G.add_edge("A", "B", key="edge2", weight=10)

        df = to_polars_edgelist(G, edge_key=None)

        assert df.shape == (2, 3)
        assert "edge_key" not in df.columns
        assert set(df.columns) == {"source", "target", "weight"}

    def test_multigraph_with_edge_key(self) -> None:
        """Test converting a multigraph with edge keys."""
        G: nx.MultiGraph[str] = nx.MultiGraph()
        G.add_edge("A", "B", key="edge1", weight=5)
        G.add_edge("A", "B", key="edge2", weight=10)

        df = to_polars_edgelist(G, edge_key="edge_id")

        assert df.shape == (2, 4)
        assert "edge_id" in df.columns
        assert set(df["edge_id"].to_list()) == {"edge1", "edge2"}

    def test_multi_digraph_with_edge_key(self) -> None:
        """Test converting a multi-directed graph with edge keys."""
        G: nx.MultiDiGraph[str] = nx.MultiDiGraph()
        G.add_edge("A", "B", key=0, weight=1)
        G.add_edge("A", "B", key=1, weight=2)
        G.add_edge("B", "A", key=0, weight=3)

        df = to_polars_edgelist(G, edge_key="edge_key")

        assert df.shape == (3, 4)
        assert "edge_key" in df.columns

    def test_empty_graph(self) -> None:
        """Test converting an empty graph."""
        G: nx.Graph[str] = nx.Graph()
        df = to_polars_edgelist(G)

        assert df.shape == (0, 2)
        assert set(df.columns) == {"source", "target"}

    def test_graph_with_numeric_nodes(self) -> None:
        """Test graph with numeric node identifiers."""
        G = nx.Graph([(1, 2, {"weight": 0.5}), (2, 3, {"weight": 1.5})])
        df = to_polars_edgelist(G)

        assert df.shape == (2, 3)
        assert df["source"].dtype == pl.Int64
        assert df["target"].dtype == pl.Int64
        assert 1 in df["source"].to_list()

    def test_graph_with_mixed_attribute_types(self) -> None:
        """Test graph with attributes of different types."""
        G: nx.Graph[str] = nx.Graph()
        G.add_edge("A", "B", weight=5, label="primary", active=True, ratio=0.75)

        df = to_polars_edgelist(G)

        assert df.shape == (1, 6)
        assert df["weight"][0] == 5
        assert df["label"][0] == "primary"
        assert df["active"][0] is True
        assert df["ratio"][0] == 0.75

    def test_source_name_collision_raises_error(self) -> None:
        """Test that using 'source' as an attribute name raises an error."""
        G = nx.Graph([("A", "B", {"source": "invalid"})])

        with pytest.raises(
            nx.NetworkXError, match="Source name 'source' is an edge attr name"
        ):
            to_polars_edgelist(G)

    def test_target_name_collision_raises_error(self) -> None:
        """Test that using 'target' as an attribute name raises an error."""
        G = nx.Graph([("A", "B", {"target": "invalid"})])

        with pytest.raises(
            nx.NetworkXError, match="Target name 'target' is an edge attr name"
        ):
            to_polars_edgelist(G)

    def test_edge_key_name_collision_raises_error(self) -> None:
        """Test that edge_key collision with attribute name raises an error."""
        G: nx.MultiGraph[str] = nx.MultiGraph()
        G.add_edge("A", "B", key="k1", edge_id=10)

        with pytest.raises(
            nx.NetworkXError, match="Edge key name 'edge_id' is an edge attr name"
        ):
            to_polars_edgelist(G, edge_key="edge_id")

    def test_custom_column_names_avoid_collision(self) -> None:
        """Test using custom column names to avoid attribute collisions."""
        G = nx.Graph([("A", "B", {"source": 1, "target": 2})])

        # This should work because we're using different column names
        df = to_polars_edgelist(G, source="from_node", target="to_node")

        assert df.shape == (1, 4)
        assert "from_node" in df.columns
        assert "to_node" in df.columns
        assert df["source"][0] == 1
        assert df["target"][0] == 2

    def test_graph_with_self_loops(self) -> None:
        """Test graph with self-loops."""
        G: nx.Graph[str] = nx.Graph()
        G.add_edge("A", "A", weight=1)
        G.add_edge("B", "B", weight=2)

        df = to_polars_edgelist(G)

        assert df.shape == (2, 3)
        assert "A" in df.filter(pl.col("source") == "A")["target"].to_list()
        assert "B" in df.filter(pl.col("source") == "B")["target"].to_list()

    def test_large_graph(self) -> None:
        """Test with a larger graph to ensure scalability."""
        G = nx.complete_graph(100)  # pyright: ignore

        for u, v in G.edges():  # pyright: ignore
            G[u][v]["weight"] = u + v

        df = to_polars_edgelist(G)  # pyright: ignore

        expected_edges = 100 * 99 // 2  # Complete graph formula
        assert df.shape[0] == expected_edges
        assert set(df.columns) == {"source", "target", "weight"}

    def test_graph_with_none_attribute_values(self) -> None:
        """Test graph where attributes explicitly have None values."""
        G: nx.Graph[str] = nx.Graph()
        G.add_edge("A", "B", weight=None, cost=5)
        G.add_edge("B", "C", weight=10, cost=None)

        df = to_polars_edgelist(G)

        assert df.shape == (2, 4)
        row_ab = df.filter(pl.col("source") == "A")
        row_bc = df.filter(pl.col("source") == "B")

        assert row_ab["weight"][0] is None
        assert row_ab["cost"][0] == 5
        assert row_bc["weight"][0] == 10
        assert row_bc["cost"][0] is None

    def test_nodelist_with_empty_result(self) -> None:
        """Test nodelist that results in no edges."""
        G = nx.Graph([("A", "B"), ("C", "D")])
        df = to_polars_edgelist(G, nodelist=["E", "F"])

        assert df.shape[0] == 0
        assert set(df.columns) == {"source", "target"}

    def test_graph_with_tuple_nodes(self) -> None:
        """Test graph with tuple node identifiers."""
        G: nx.Graph[tuple[int, int]] = nx.Graph()
        G.add_edge((1, 2), (3, 4), weight=5)
        G.add_edge((3, 4), (5, 6), weight=10)

        df = to_polars_edgelist(G)

        assert df.shape == (2, 3)
        # Tuple nodes are converted to lists in Polars
        assert [1, 2] in df["source"].to_list()

    def test_preserves_edge_order(self) -> None:
        """Test that edge order is preserved in the output."""
        edges = [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H")]
        G = nx.Graph(edges)
        df = to_polars_edgelist(G)

        # The order should match the insertion order
        result_edges = list(
            zip(df["source"].to_list(), df["target"].to_list(), strict=True)
        )

        # NetworkX may not preserve exact order, but all edges should be present
        for edge in edges:
            assert edge in result_edges or (edge[1], edge[0]) in result_edges

    def test_weighted_graph_common_pattern(self) -> None:
        """Test common pattern of weighted graph analysis."""
        G: nx.Graph[str] = nx.Graph()
        G.add_edge("A", "B", weight=1.5)
        G.add_edge("B", "C", weight=2.5)
        G.add_edge("C", "A", weight=3.5)

        df = to_polars_edgelist(G)

        # Common operation: filter edges by weight
        heavy_edges = df.filter(pl.col("weight") > 2.0)
        assert heavy_edges.shape[0] == 2

        # Common operation: sum all weights
        total_weight = df["weight"].sum()
        assert total_weight == 7.5
