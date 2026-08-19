# SPDX-License-Identifier: MIT
"""Tests for the DiGraph container."""

from __future__ import annotations

import pytest

from ece608.toposort import DiGraph, NodeNotFound


def test_add_node_is_idempotent():
    g = DiGraph()
    g.add_node("a")
    g.add_node("a")
    assert len(g) == 1


def test_none_is_not_a_node():
    with pytest.raises(ValueError):
        DiGraph().add_node(None)


def test_add_edge_creates_endpoints():
    g = DiGraph()
    g.add_edge("a", "b")
    assert set(g.nodes) == {"a", "b"}
    assert g.has_edge("a", "b")
    assert not g.has_edge("b", "a")


def test_degrees_stay_consistent():
    g = DiGraph([("a", "c"), ("b", "c"), ("c", "d")])
    assert g.in_degree("c") == 2
    assert g.out_degree("c") == 1
    assert g.in_degree("a") == 0
    assert g.out_degree("d") == 0


def test_remove_node_cleans_both_directions():
    """The predecessor mirror is the thing most likely to go stale."""
    g = DiGraph([("a", "b"), ("b", "c")])
    g.remove_node("b")
    assert set(g.nodes) == {"a", "c"}
    assert g.out_degree("a") == 0
    assert g.in_degree("c") == 0
    assert g.number_of_edges() == 0


def test_remove_edge_updates_predecessors():
    g = DiGraph([("a", "b")])
    g.remove_edge("a", "b")
    assert g.in_degree("b") == 0
    assert list(g.predecessors("b")) == []


def test_missing_node_raises():
    g = DiGraph()
    for call in (
        lambda: g.remove_node("nope"),
        lambda: g.in_degree("nope"),
        lambda: g.out_degree("nope"),
        lambda: list(g.successors("nope")),
        lambda: list(g.predecessors("nope")),
    ):
        with pytest.raises(NodeNotFound):
            call()


def test_duplicate_edges_do_not_inflate_degree():
    g = DiGraph()
    g.add_edge("a", "b")
    g.add_edge("a", "b")
    assert g.number_of_edges() == 1
    assert g.in_degree("b") == 1


def test_attributes_round_trip():
    g = DiGraph()
    g.add_node("a", label="start")
    g.add_edge("a", "b", weight=3)
    assert g.node_data("a")["label"] == "start"
    assert g.edge_data("a", "b")["weight"] == 3


def test_insertion_order_is_preserved():
    g = DiGraph()
    g.add_nodes_from("zyxw")
    assert list(g.nodes) == list("zyxw")


def test_reverse():
    g = DiGraph([("a", "b"), ("b", "c")])
    r = g.reverse()
    assert set(r.edges) == {("b", "a"), ("c", "b")}
    assert set(r.nodes) == set(g.nodes)


def test_copy_is_independent():
    g = DiGraph([("a", "b")])
    h = g.copy()
    h.add_edge("b", "c")
    assert g.number_of_nodes() == 2
    assert h.number_of_nodes() == 3


def test_from_adjacency_keeps_sinks():
    g = DiGraph.from_adjacency({"a": ["b"], "b": [], "c": []})
    assert set(g.nodes) == {"a", "b", "c"}


def test_matrix_round_trip():
    m = [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    g = DiGraph.from_matrix(m, labels="abc")
    assert set(g.edges) == {("a", "b"), ("b", "c")}
    assert g.to_matrix(labels="abc") == m


def test_matrix_records_weights():
    g = DiGraph.from_matrix([[0, 5], [0, 0]], labels="ab")
    assert g.edge_data("a", "b")["weight"] == 5


def test_matrix_validates_shape():
    with pytest.raises(ValueError):
        DiGraph.from_matrix([[0, 1], [0]])
    with pytest.raises(ValueError):
        DiGraph.from_matrix([[0, 1], [0, 0]], labels="abc")


def test_contains_handles_unhashable():
    g = DiGraph([("a", "b")])
    assert "a" in g
    assert ["not", "hashable"] not in g


def test_repr_is_useful():
    g = DiGraph([("a", "b")], name="wardrobe")
    assert "wardrobe" in repr(g)
    assert "2 nodes" in repr(g)
