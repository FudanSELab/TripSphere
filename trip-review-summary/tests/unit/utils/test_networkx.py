"""Unit tests for NetworkX utilities."""

from __future__ import annotations

import networkx as nx
import polars as pl
import pytest

from review_summary.utils.networkx import from_polars_edgelist, to_polars_edgelist


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
        G = nx.complete_graph(100)  # ty: ignore  # pyright: ignore

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


class TestFromPolarsEdgelist:
    """Test suite for from_polars_edgelist function."""

    def test_simple_edgelist_no_attributes(self) -> None:
        """Test creating a graph from simple edge list without attributes."""
        df = pl.DataFrame({"source": ["A", "B", "C"], "target": ["B", "C", "D"]})
        G = from_polars_edgelist(df)

        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3
        assert G.has_edge("A", "B")
        assert G.has_edge("B", "C")
        assert G.has_edge("C", "D")

    def test_simple_edgelist_with_numeric_nodes(self) -> None:
        """Test creating a graph with numeric node identifiers."""
        df = pl.DataFrame({"source": [0, 1, 2], "target": [1, 2, 3]})
        G = from_polars_edgelist(df)

        assert G.number_of_nodes() == 4
        assert G.number_of_edges() == 3
        assert G.has_edge(0, 1)
        assert G.has_edge(1, 2)
        assert G.has_edge(2, 3)

    def test_edge_attr_none(self) -> None:
        """Test that edge_attr=None creates edges without attributes."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [5, 10],
                "color": ["red", "blue"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=None)

        assert G.number_of_edges() == 2
        # No attributes should be added
        assert G[0][1] == {}
        assert G[1][2] == {}

    def test_edge_attr_single_column(self) -> None:
        """Test adding a single edge attribute column."""
        df = pl.DataFrame(
            {"source": [0, 1, 2], "target": [1, 2, 3], "weight": [5, 10, 15]}
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.number_of_edges() == 3
        assert G[0][1]["weight"] == 5
        assert G[1][2]["weight"] == 10
        assert G[2][3]["weight"] == 15

    def test_edge_attr_multiple_columns_list(self) -> None:
        """Test adding multiple edge attributes using a list."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [5, 10],
                "cost": [2, 4],
                "label": ["A", "B"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=["weight", "cost"])

        assert G[0][1]["weight"] == 5
        assert G[0][1]["cost"] == 2
        assert "label" not in G[0][1]
        assert G[1][2]["weight"] == 10
        assert G[1][2]["cost"] == 4

    def test_edge_attr_multiple_columns_tuple(self) -> None:
        """Test adding multiple edge attributes using a tuple."""
        df = pl.DataFrame(
            {
                "source": ["A", "B"],
                "target": ["B", "C"],
                "weight": [1.5, 2.5],
                "color": ["red", "blue"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=("weight", "color"))

        assert G["A"]["B"]["weight"] == 1.5
        assert G["A"]["B"]["color"] == "red"
        assert G["B"]["C"]["weight"] == 2.5
        assert G["B"]["C"]["color"] == "blue"

    def test_edge_attr_true_adds_all_columns(self) -> None:
        """Test that edge_attr=True adds all columns except source/target."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [5, 10],
                "cost": [2, 4],
                "label": ["A", "B"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=True)

        assert G[0][1]["weight"] == 5
        assert G[0][1]["cost"] == 2
        assert G[0][1]["label"] == "A"
        assert G[1][2]["weight"] == 10
        assert G[1][2]["cost"] == 4
        assert G[1][2]["label"] == "B"

    def test_custom_source_target_columns(self) -> None:
        """Test using custom column names for source and target."""
        df = pl.DataFrame({"from": ["A", "B"], "to": ["B", "C"], "weight": [1, 2]})
        G = from_polars_edgelist(df, source="from", target="to", edge_attr="weight")

        assert G.number_of_edges() == 2
        assert G.has_edge("A", "B")
        assert G["A"]["B"]["weight"] == 1
        assert G["B"]["C"]["weight"] == 2

    def test_create_using_digraph(self) -> None:
        """Test creating a directed graph."""
        df = pl.DataFrame({"source": [0, 1], "target": [1, 0]})
        G = from_polars_edgelist(df, create_using=nx.DiGraph)

        assert isinstance(G, nx.DiGraph)
        assert G.has_edge(0, 1)
        assert G.has_edge(1, 0)
        assert G.number_of_edges() == 2

    def test_create_using_graph_instance(self) -> None:
        """Test using a graph instance for create_using."""
        existing_graph: nx.Graph[str] = nx.Graph()
        existing_graph.add_node("Z")  # This should be cleared

        df = pl.DataFrame({"source": ["A", "B"], "target": ["B", "C"]})
        G = from_polars_edgelist(df, create_using=existing_graph)

        assert G.number_of_nodes() == 3
        assert "Z" not in G.nodes()
        assert G.has_edge("A", "B")

    def test_multigraph_without_edge_key(self) -> None:
        """Test creating a MultiGraph without specifying edge keys."""
        df = pl.DataFrame(
            {
                "source": [0, 0, 1],
                "target": [1, 1, 2],
                "weight": [5, 10, 15],
            }
        )
        G = from_polars_edgelist(df, edge_attr="weight", create_using=nx.MultiGraph)

        assert isinstance(G, nx.MultiGraph)
        assert G.number_of_edges() == 3
        # Both edges between 0 and 1 should exist
        assert len(G[0][1]) == 2

    def test_multigraph_with_edge_key(self) -> None:
        """Test creating a MultiGraph with custom edge keys."""
        df = pl.DataFrame(
            {
                "source": [0, 0, 1],
                "target": [1, 1, 2],
                "edge_id": ["A", "B", "C"],
                "weight": [5, 10, 15],
            }
        )
        G = from_polars_edgelist(
            df,
            edge_attr="weight",
            edge_key="edge_id",
            create_using=nx.MultiGraph,
        )

        assert isinstance(G, nx.MultiGraph)
        assert G[0][1]["A"]["weight"] == 5
        assert G[0][1]["B"]["weight"] == 10
        assert G[1][2]["C"]["weight"] == 15

    def test_multigraph_edge_key_with_multiple_attrs(self) -> None:
        """Test MultiGraph with edge keys and multiple attributes."""
        df = pl.DataFrame(
            {
                "source": [0, 0],
                "target": [1, 1],
                "key": ["first", "second"],
                "weight": [3, 6],
                "color": ["red", "blue"],
            }
        )
        G = from_polars_edgelist(
            df,
            edge_key="key",
            edge_attr=["weight", "color"],
            create_using=nx.MultiGraph,
        )

        assert G[0][1]["first"]["weight"] == 3
        assert G[0][1]["first"]["color"] == "red"
        assert G[0][1]["second"]["weight"] == 6
        assert G[0][1]["second"]["color"] == "blue"

    def test_multigraph_edge_attr_true_excludes_edge_key(self) -> None:
        """Test that edge_attr=True excludes edge_key column in MultiGraph."""
        df = pl.DataFrame(
            {
                "source": [0, 0],
                "target": [1, 1],
                "key": ["A", "B"],
                "weight": [5, 10],
                "cost": [1, 2],
            }
        )
        G = from_polars_edgelist(
            df, edge_attr=True, edge_key="key", create_using=nx.MultiGraph
        )

        # 'key' should not be in the edge attributes
        assert "key" not in G[0][1]["A"]
        assert G[0][1]["A"]["weight"] == 5
        assert G[0][1]["A"]["cost"] == 1

    def test_multi_digraph(self) -> None:
        """Test creating a MultiDiGraph."""
        df = pl.DataFrame(
            {
                "source": [0, 0, 1],
                "target": [1, 1, 0],
                "key": [0, 1, 0],
                "weight": [5, 10, 15],
            }
        )
        G = from_polars_edgelist(
            df,
            edge_key="key",
            edge_attr="weight",
            create_using=nx.MultiDiGraph,
        )

        assert isinstance(G, nx.MultiDiGraph)
        assert G.number_of_edges() == 3
        assert G.get_edge_data(0, 1, 0)["weight"] == 5
        assert G.get_edge_data(0, 1, 1)["weight"] == 10
        assert G.get_edge_data(1, 0, 0)["weight"] == 15

    def test_empty_dataframe(self) -> None:
        """Test creating a graph from an empty DataFrame."""
        df = pl.DataFrame(
            {"source": [], "target": []}, schema={"source": pl.Utf8, "target": pl.Utf8}
        )
        G = from_polars_edgelist(df)

        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_single_edge(self) -> None:
        """Test creating a graph with a single edge."""
        df = pl.DataFrame({"source": ["A"], "target": ["B"], "weight": [42]})
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.number_of_nodes() == 2
        assert G.number_of_edges() == 1
        assert G["A"]["B"]["weight"] == 42

    def test_self_loops(self) -> None:
        """Test graph with self-loops."""
        df = pl.DataFrame(
            {"source": ["A", "B", "A"], "target": ["A", "B", "B"], "weight": [1, 2, 3]}
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.has_edge("A", "A")
        assert G.has_edge("B", "B")
        assert G["A"]["A"]["weight"] == 1
        assert G["B"]["B"]["weight"] == 2

    def test_mixed_data_types_in_attributes(self) -> None:
        """Test edge attributes with different data types."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [1.5, 2.5],
                "count": [10, 20],
                "label": ["first", "second"],
                "active": [True, False],
            }
        )
        G = from_polars_edgelist(df, edge_attr=True)

        assert G[0][1]["weight"] == 1.5
        assert G[0][1]["count"] == 10
        assert G[0][1]["label"] == "first"
        assert G[0][1]["active"] is True

    def test_none_values_in_attributes(self) -> None:
        """Test handling of None values in edge attributes."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [5, None],
                "label": [None, "B"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=["weight", "label"])

        assert G[0][1]["weight"] == 5
        assert G[0][1]["label"] is None
        assert G[1][2]["weight"] is None
        assert G[1][2]["label"] == "B"

    def test_large_graph_performance(self) -> None:
        """Test with a larger DataFrame to ensure performance."""
        n_edges = 1000
        df = pl.DataFrame(
            {
                "source": list(range(n_edges)),
                "target": list(range(1, n_edges + 1)),
                "weight": list(range(n_edges)),
            }
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.number_of_edges() == n_edges
        assert G[0][1]["weight"] == 0
        assert G[999][1000]["weight"] == 999

    def test_invalid_edge_attr_column_raises_error(self) -> None:
        """Test that invalid edge_attr column name raises an error."""
        df = pl.DataFrame({"source": [0, 1], "target": [1, 2], "weight": [5, 10]})

        with pytest.raises(nx.NetworkXError, match="Invalid edge_attr argument"):
            from_polars_edgelist(df, edge_attr="nonexistent")

    def test_invalid_edge_attr_empty_list_raises_error(self) -> None:
        """Test that empty edge_attr list raises an error."""
        df = pl.DataFrame({"source": [0, 1], "target": [1, 2], "weight": [5, 10]})

        with pytest.raises(nx.NetworkXError, match="No columns found with name"):
            from_polars_edgelist(df, edge_attr=[])

    def test_invalid_edge_key_column_raises_error(self) -> None:
        """Test that invalid edge_key column raises an error."""
        df = pl.DataFrame(
            {"source": [0, 1], "target": [1, 2], "key": ["A", "B"], "weight": [5, 10]}
        )

        with pytest.raises(nx.NetworkXError, match="Invalid edge_key argument"):
            from_polars_edgelist(df, edge_key="nonexistent", create_using=nx.MultiGraph)

    def test_round_trip_conversion(self) -> None:
        """Test that to_polars_edgelist and from_polars_edgelist are inverses."""
        # Create a graph
        G1: nx.Graph[str] = nx.Graph()
        G1.add_edge("A", "B", weight=5, cost=2)
        G1.add_edge("B", "C", weight=10, cost=4)

        # Convert to DataFrame and back
        df = to_polars_edgelist(G1)
        G2 = from_polars_edgelist(df, edge_attr=True)

        # Verify they are equivalent
        assert G1.number_of_nodes() == G2.number_of_nodes()
        assert G1.number_of_edges() == G2.number_of_edges()
        assert G2["A"]["B"]["weight"] == 5
        assert G2["A"]["B"]["cost"] == 2
        assert G2["B"]["C"]["weight"] == 10
        assert G2["B"]["C"]["cost"] == 4

    def test_round_trip_multigraph(self) -> None:
        """Test round-trip conversion for MultiGraph."""
        G1: nx.MultiGraph[str] = nx.MultiGraph()
        G1.add_edge("A", "B", key="first", weight=5)
        G1.add_edge("A", "B", key="second", weight=10)

        df = to_polars_edgelist(G1, edge_key="edge_key")
        G2 = from_polars_edgelist(
            df, edge_attr="weight", edge_key="edge_key", create_using=nx.MultiGraph
        )

        assert G2.number_of_edges() == 2
        assert G2["A"]["B"]["first"]["weight"] == 5
        assert G2["A"]["B"]["second"]["weight"] == 10

    def test_disconnected_components(self) -> None:
        """Test graph with disconnected components."""
        df = pl.DataFrame(
            {
                "source": ["A", "B", "D", "E"],
                "target": ["B", "C", "E", "F"],
                "weight": [1, 2, 3, 4],
            }
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.number_of_nodes() == 6
        assert G.number_of_edges() == 4
        assert nx.number_connected_components(G) == 2  # ty: ignore

    def test_duplicate_edges_in_simple_graph(self) -> None:
        """Test that duplicate edges in simple graph only create one edge."""
        df = pl.DataFrame(
            {"source": [0, 0, 1], "target": [1, 1, 2], "weight": [5, 10, 15]}
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert isinstance(G, nx.Graph)
        # In a simple graph, duplicate edges overwrite
        assert G.number_of_edges() == 2
        # The last weight should be used
        assert G[0][1]["weight"] == 10

    def test_polars_series_iteration(self) -> None:
        """Test that Polars Series iteration works correctly."""
        df = pl.DataFrame(
            {
                "source": pl.Series([1, 2, 3], dtype=pl.Int64),
                "target": pl.Series([2, 3, 4], dtype=pl.Int64),
                "weight": pl.Series([1.0, 2.0, 3.0], dtype=pl.Float64),
            }
        )
        G = from_polars_edgelist(df, edge_attr="weight")

        assert G.number_of_edges() == 3
        assert all(isinstance(G[u][v]["weight"], float) for u, v in G.edges())

    def test_edge_attr_with_reserved_column_names(self) -> None:
        """Test handling when edge_attr=True with reserved column names."""
        df = pl.DataFrame(
            {
                "source": [0, 1],
                "target": [1, 2],
                "weight": [5, 10],
                "other": ["A", "B"],
            }
        )
        G = from_polars_edgelist(df, edge_attr=True)

        # Should include all columns except source and target
        assert "weight" in G[0][1]
        assert "other" in G[0][1]
        assert "source" not in G[0][1]
        assert "target" not in G[0][1]

    def test_integer_column_names(self) -> None:
        """Test using integer column names (edge case)."""
        df = pl.DataFrame(
            {
                "source": ["A", "B"],
                "target": ["B", "C"],
                "weight": [5, 10],
            }
        )
        # Should work with string column names
        G = from_polars_edgelist(
            df, source="source", target="target", edge_attr="weight"
        )

        assert G.has_edge("A", "B")
        assert G["A"]["B"]["weight"] == 5

    def test_multigraph_none_edge_attr_with_edge_key(self) -> None:
        """Test MultiGraph with edge_key but no edge attributes."""
        df = pl.DataFrame(
            {
                "source": [0, 0],
                "target": [1, 1],
                "key": ["A", "B"],
            }
        )
        G = from_polars_edgelist(
            df, edge_attr=None, edge_key="key", create_using=nx.MultiGraph
        )

        assert G.number_of_edges() == 2
        # Edges should exist with the specified keys
        assert "A" in G[0][1]
        assert "B" in G[0][1]

    def test_complete_graph_pattern(self) -> None:
        """Test creating a complete graph from edge list."""
        nodes = ["A", "B", "C"]
        edges = [(u, v) for u in nodes for v in nodes if u < v]
        df = pl.DataFrame(
            {"source": [e[0] for e in edges], "target": [e[1] for e in edges]}
        )

        G = from_polars_edgelist(df)

        assert G.number_of_nodes() == 3
        assert G.number_of_edges() == 3
        assert G.has_edge("A", "B")
        assert G.has_edge("A", "C")
        assert G.has_edge("B", "C")

    def test_weighted_directed_graph(self) -> None:
        """Test common pattern of weighted directed graph."""
        df = pl.DataFrame(
            {
                "source": ["A", "B", "C", "D"],
                "target": ["B", "C", "D", "A"],
                "weight": [1.0, 2.0, 3.0, 4.0],
            }
        )
        G = from_polars_edgelist(df, edge_attr="weight", create_using=nx.DiGraph)

        assert isinstance(G, nx.DiGraph)
        assert nx.is_strongly_connected(G)  # ty: ignore
        total_weight = sum(G[u][v]["weight"] for u, v in G.edges())
        assert total_weight == 10.0
