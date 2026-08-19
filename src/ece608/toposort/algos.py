# SPDX-FileCopyrightText: 2022-present Santosh Ahuja <ahuja28@purdue.edu>
# SPDX-License-Identifier: MIT
"""Topological ordering by two routes, plus the cycle machinery they need.

Both algorithms are O(V + E) time and O(V) auxiliary space, and both are
iterative — no recursion, so a path of 10^6 nodes will not exhaust the
interpreter stack the way a textbook recursive DFS does.

They differ in what they give you beyond the order:

``kahn``
    Peels sources off a frontier. Naturally incremental, and the partially
    consumed frontier tells you *where* a cycle is without a second pass.
    Accepts a ``key`` for deterministic tie-breaking, which is what you want
    when the order feeds a build system or a test fixture.

``dfs_topological_sort``
    Reverse postorder of a depth-first forest (CLRS 22.4). Produces the
    reverse-postorder numbering that dominator and SCC algorithms build on,
    so it is the one to extend.

For a DAG the set of valid orders is usually large; neither function is
"more correct" than the other. :func:`is_topological_order` is the predicate
that actually decides validity, and the test suite uses it rather than
comparing against a golden sequence.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Hashable, Iterator, Sequence
from typing import Any

from .exceptions import CycleError
from .graph import DiGraph

__all__ = [
    "dfs_topological_sort",
    "find_cycle",
    "is_dag",
    "is_topological_order",
    "kahn",
    "layers",
    "longest_path_length",
]

Node = Hashable

# node colours for the iterative DFS
_WHITE, _GREY, _BLACK = 0, 1, 2


def kahn(graph: DiGraph, key: Callable[[Node], Any] | None = None) -> list[Node]:
    """Topological order by repeatedly removing in-degree-zero nodes.

    Kahn (1962). O(V + E) time, O(V) space.

    Args:
        graph: the graph to order.
        key: optional sort key applied to the frontier. Without it the order
            follows insertion order, which is already deterministic. With it
            you get a *stable, content-defined* order — the same graph built
            in a different order yields the same result. That costs
            O(V log V) overall.

    Returns:
        A list containing every node exactly once, with every edge ``u -> v``
        placing ``u`` before ``v``.

    Raises:
        CycleError: if the graph is cyclic. The reported cycle is drawn from
            the nodes that never reached in-degree zero.

    >>> g = DiGraph([("a", "b"), ("b", "c"), ("a", "c")])
    >>> kahn(g)
    ['a', 'b', 'c']
    """
    in_degree = {n: graph.in_degree(n) for n in graph}
    ready = [n for n, d in in_degree.items() if d == 0]

    order: list[Node] = []
    if key is None:
        frontier = deque(ready)
        pop = frontier.popleft
        push = frontier.append
    else:
        import heapq

        heap = [(key(n), i, n) for i, n in enumerate(ready)]
        heapq.heapify(heap)
        counter = len(heap)

        def pop() -> Node:                    # type: ignore[misc]
            return heapq.heappop(heap)[2]

        def push(n: Node) -> None:            # type: ignore[misc]
            nonlocal counter
            heapq.heappush(heap, (key(n), counter, n))
            counter += 1

        frontier = heap                       # type: ignore[assignment]

    while frontier:
        n = pop()
        order.append(n)
        for m in graph.successors(n):
            in_degree[m] -= 1
            if in_degree[m] == 0:
                push(m)

    if len(order) != len(graph):
        # Whatever never drained is inside, or downstream of, a cycle.
        stuck = DiGraph()
        for n, d in in_degree.items():
            if d > 0:
                stuck.add_node(n)
        for u in stuck.nodes:
            for v in graph.successors(u):
                if v in stuck:
                    stuck.add_edge(u, v)
        raise CycleError(find_cycle(stuck) or list(stuck.nodes)[:1])

    return order


def dfs_topological_sort(graph: DiGraph) -> list[Node]:
    """Topological order as the reverse postorder of a DFS forest.

    CLRS 22.4. O(V + E) time, O(V) space. Iterative, so depth is bounded by
    heap rather than by the interpreter's recursion limit.

    Raises:
        CycleError: on the first back edge encountered, reporting the cycle.

    >>> g = DiGraph([("a", "b"), ("b", "c")])
    >>> dfs_topological_sort(g)
    ['a', 'b', 'c']
    """
    colour: dict[Node, int] = {n: _WHITE for n in graph}
    postorder: list[Node] = []
    on_path: list[Node] = []          # the current grey chain, for cycle reporting

    for root in graph:
        if colour[root] != _WHITE:
            continue
        # each frame: (node, iterator over its successors)
        stack: list[tuple[Node, Iterator[Node]]] = [(root, graph.successors(root))]
        colour[root] = _GREY
        on_path.append(root)

        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if colour[child] == _WHITE:
                    colour[child] = _GREY
                    on_path.append(child)
                    stack.append((child, graph.successors(child)))
                    advanced = True
                    break
                if colour[child] == _GREY:
                    # back edge: the cycle is the grey chain from child onward
                    start = on_path.index(child)
                    raise CycleError([*on_path[start:], child])
            if not advanced:
                colour[node] = _BLACK
                postorder.append(node)
                on_path.pop()
                stack.pop()

    postorder.reverse()
    return postorder


def is_topological_order(graph: DiGraph, order: Sequence[Node]) -> bool:
    """True when ``order`` lists every node once and respects every edge.

    This is the property worth testing. Comparing a sort against one golden
    sequence tests the tie-breaking, not the correctness — a DAG generally
    admits many valid orders.

    O(V + E).
    """
    if len(order) != len(graph):
        return False
    position = {n: i for i, n in enumerate(order)}
    if len(position) != len(order):        # duplicates
        return False
    if any(n not in position for n in graph):
        return False
    return all(position[u] < position[v] for u, v in graph.edges)


def find_cycle(graph: DiGraph) -> list[Node] | None:
    """Return one cycle as a node list, or ``None`` if the graph is acyclic.

    The returned list repeats its first node at the end, so ``a -> b -> a``
    comes back as ``['a', 'b', 'a']``. O(V + E).
    """
    colour: dict[Node, int] = {n: _WHITE for n in graph}

    for root in graph:
        if colour[root] != _WHITE:
            continue
        on_path: list[Node] = [root]
        colour[root] = _GREY
        stack: list[tuple[Node, Iterator[Node]]] = [(root, graph.successors(root))]
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if colour[child] == _WHITE:
                    colour[child] = _GREY
                    on_path.append(child)
                    stack.append((child, graph.successors(child)))
                    advanced = True
                    break
                if colour[child] == _GREY:
                    return [*on_path[on_path.index(child):], child]
            if not advanced:
                colour[node] = _BLACK
                on_path.pop()
                stack.pop()
    return None


def is_dag(graph: DiGraph) -> bool:
    """True when the graph has no directed cycle. O(V + E)."""
    return find_cycle(graph) is None


def layers(graph: DiGraph) -> list[list[Node]]:
    """Partition into ranks: layer *i* holds nodes whose longest path in is *i*.

    Everything in a layer is mutually independent, so this is the schedule you
    want for parallel execution — layer *i* can run only after *i-1*, and can
    run entirely concurrently within itself.

    O(V + E). Raises :class:`CycleError` on a cyclic graph.

    >>> g = DiGraph([("a", "c"), ("b", "c"), ("c", "d")])
    >>> layers(g)
    [['a', 'b'], ['c'], ['d']]
    """
    in_degree = {n: graph.in_degree(n) for n in graph}
    current = [n for n, d in in_degree.items() if d == 0]
    out: list[list[Node]] = []
    seen = 0
    while current:
        out.append(current)
        seen += len(current)
        nxt: list[Node] = []
        for n in current:
            for m in graph.successors(n):
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    nxt.append(m)
        current = nxt
    if seen != len(graph):
        raise CycleError(find_cycle(graph) or [])
    return out


def longest_path_length(graph: DiGraph) -> int:
    """Edges on the longest path in the DAG — the critical-path length.

    Equal to ``len(layers(graph)) - 1`` for a non-empty graph, and the lower
    bound on how many sequential steps the graph can be executed in.
    """
    if len(graph) == 0:
        return 0
    return len(layers(graph)) - 1
