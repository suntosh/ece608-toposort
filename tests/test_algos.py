# SPDX-License-Identifier: MIT
"""Tests for the ordering algorithms.

The central idea: a DAG admits many valid topological orders, so asserting
against one golden sequence tests tie-breaking rather than correctness. These
tests assert the *property* — every node once, every edge respected — via
``is_topological_order``, and cross-check the two algorithms against it.
"""

from __future__ import annotations

import random

import pytest

from ece608.toposort import (
    CycleError,
    DiGraph,
    dfs_topological_sort,
    find_cycle,
    is_dag,
    is_topological_order,
    kahn,
    layers,
    longest_path_length,
)

SORTS = (kahn, dfs_topological_sort)


def random_dag(n: int, density: float, seed: int) -> DiGraph:
    """A random DAG: edges only ever run low index -> high index."""
    rng = random.Random(seed)
    g = DiGraph()
    order = list(range(n))
    rng.shuffle(order)
    g.add_nodes_from(order)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < density:
                g.add_edge(order[i], order[j])
    return g


# --------------------------------------------------------------- basic shape

@pytest.mark.parametrize("sort", SORTS)
def test_empty_graph(sort):
    assert sort(DiGraph()) == []


@pytest.mark.parametrize("sort", SORTS)
def test_single_node(sort):
    g = DiGraph()
    g.add_node("only")
    assert sort(g) == ["only"]


@pytest.mark.parametrize("sort", SORTS)
def test_no_edges_keeps_every_node(sort):
    g = DiGraph()
    g.add_nodes_from("abcde")
    assert sorted(sort(g)) == list("abcde")


@pytest.mark.parametrize("sort", SORTS)
def test_chain(sort):
    g = DiGraph([(i, i + 1) for i in range(50)])
    assert sort(g) == list(range(51))


@pytest.mark.parametrize("sort", SORTS)
def test_disconnected_components(sort):
    g = DiGraph([("a", "b"), ("x", "y")])
    assert is_topological_order(g, sort(g))


@pytest.mark.parametrize("sort", SORTS)
def test_isolated_sink_is_not_dropped(sort):
    """A node that appears only as a dict key must still be ordered."""
    g = DiGraph.from_adjacency({"a": ["b"], "b": [], "c": []})
    assert sorted(sort(g)) == ["a", "b", "c"]


# ------------------------------------------------------------------ property

@pytest.mark.parametrize("sort", SORTS)
@pytest.mark.parametrize("seed", range(25))
def test_random_dags_produce_valid_orders(sort, seed):
    g = random_dag(n=40, density=0.08, seed=seed)
    assert is_topological_order(g, sort(g))


@pytest.mark.parametrize("seed", range(15))
def test_both_algorithms_agree_on_validity(seed):
    g = random_dag(n=30, density=0.12, seed=seed)
    a, b = kahn(g), dfs_topological_sort(g)
    assert is_topological_order(g, a)
    assert is_topological_order(g, b)
    assert sorted(map(str, a)) == sorted(map(str, b))


def test_is_topological_order_rejects_bad_orders():
    g = DiGraph([("a", "b")])
    assert not is_topological_order(g, ["b", "a"])       # edge violated
    assert not is_topological_order(g, ["a"])            # missing node
    assert not is_topological_order(g, ["a", "a", "b"])  # duplicate
    assert not is_topological_order(g, ["a", "b", "z"])  # unknown node


# -------------------------------------------------------------------- cycles

@pytest.mark.parametrize("sort", SORTS)
def test_self_loop_is_a_cycle(sort):
    g = DiGraph([("a", "a")])
    with pytest.raises(CycleError):
        sort(g)


@pytest.mark.parametrize("sort", SORTS)
def test_two_node_cycle(sort):
    g = DiGraph([("a", "b"), ("b", "a")])
    with pytest.raises(CycleError):
        sort(g)


@pytest.mark.parametrize("sort", SORTS)
def test_cycle_behind_a_long_acyclic_prefix(sort):
    """The cycle is unreachable from the sources — both must still find it."""
    g = DiGraph([("s1", "s2"), ("s2", "s3")])
    g.add_edges_from([("c1", "c2"), ("c2", "c3"), ("c3", "c1")])
    with pytest.raises(CycleError):
        sort(g)


def test_cycle_error_carries_the_cycle():
    g = DiGraph([("a", "b"), ("b", "c"), ("c", "a")])
    with pytest.raises(CycleError) as exc:
        kahn(g)
    assert exc.value.cycle, "CycleError should report which nodes cycle"
    assert set(exc.value.cycle) <= {"a", "b", "c"}


def test_find_cycle_and_is_dag():
    acyclic = DiGraph([("a", "b"), ("b", "c")])
    assert find_cycle(acyclic) is None
    assert is_dag(acyclic)

    cyclic = DiGraph([("a", "b"), ("b", "c"), ("c", "a")])
    cycle = find_cycle(cyclic)
    assert cycle is not None
    assert cycle[0] == cycle[-1], "cycle should close on itself"
    assert not is_dag(cyclic)


# ------------------------------------------------------------ determinism

def test_kahn_without_key_follows_insertion_order():
    g = DiGraph([("b", "z"), ("a", "z")])
    assert kahn(g) == ["b", "a", "z"]


def test_kahn_with_key_is_content_defined():
    """Same graph, different build order, same result once a key is given."""
    g1 = DiGraph([("b", "z"), ("a", "z")])
    g2 = DiGraph([("a", "z"), ("b", "z")])
    assert kahn(g1, key=str) == kahn(g2, key=str) == ["a", "b", "z"]


def test_repeated_runs_are_stable():
    g = random_dag(n=25, density=0.1, seed=7)
    assert kahn(g) == kahn(g)
    assert dfs_topological_sort(g) == dfs_topological_sort(g)


# ---------------------------------------------------------------- layers

def test_layers_groups_independent_work():
    g = DiGraph([("a", "c"), ("b", "c"), ("c", "d")])
    assert layers(g) == [["a", "b"], ["c"], ["d"]]


def test_layers_flatten_to_a_valid_order():
    g = random_dag(n=30, density=0.1, seed=3)
    flat = [n for layer in layers(g) for n in layer]
    assert is_topological_order(g, flat)


def test_longest_path_length():
    assert longest_path_length(DiGraph()) == 0
    assert longest_path_length(DiGraph([(i, i + 1) for i in range(5)])) == 5
    g = DiGraph([("a", "c"), ("b", "c"), ("c", "d")])
    assert longest_path_length(g) == 2


def test_layers_rejects_cycles():
    with pytest.raises(CycleError):
        layers(DiGraph([("a", "b"), ("b", "a")]))


# ------------------------------------------------------------------- scale

def test_deep_chain_does_not_blow_the_stack():
    """The DFS is iterative; a recursive one dies around 1000 here."""
    n = 20_000
    g = DiGraph([(i, i + 1) for i in range(n)])
    assert dfs_topological_sort(g) == list(range(n + 1))
