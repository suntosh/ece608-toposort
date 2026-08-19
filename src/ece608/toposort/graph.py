# SPDX-FileCopyrightText: 2022-present Santosh Ahuja <ahuja28@purdue.edu>
# SPDX-License-Identifier: MIT
"""A directed graph, adjacency-list backed, with no third-party dependencies.

The container is deliberately small: it stores what the topological-sort
algorithms in :mod:`ece608.toposort.algos` need and nothing else. Insertion
order is preserved throughout (``dict`` is ordered from CPython 3.7), which is
what makes the algorithms' output deterministic and their tests meaningful.

Complexity, for ``V`` nodes and ``E`` edges:

===========================  ==========
operation                    cost
===========================  ==========
``add_node``                 O(1)
``add_edge``                 O(1)
``remove_edge``              O(1)
``remove_node``              O(deg(n))
``successors`` (iterate)     O(out-deg)
``predecessors`` (iterate)   O(in-deg)
``in_degree`` / ``out_degree``  O(1)
``__len__``                  O(1)
===========================  ==========

Predecessors are maintained eagerly in a mirror adjacency map. That doubles
the edge storage but turns ``in_degree`` into an O(1) lookup, which is what
keeps Kahn's algorithm at O(V + E) instead of O(V * E).
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator, Sequence
from typing import Any

from .exceptions import NodeNotFound

__all__ = ["DiGraph"]

Node = Hashable


class DiGraph:
    """A directed graph with optional node and edge attributes.

    >>> g = DiGraph()
    >>> g.add_edges_from([("shirt", "tie"), ("tie", "jacket")])
    >>> len(g)
    3
    >>> sorted(g.successors("shirt"))
    ['tie']
    >>> g.in_degree("jacket")
    1
    """

    __slots__ = ("_edge_attr", "_node_attr", "_pred", "_succ", "name")

    def __init__(self, edges: Iterable[Sequence[Node]] | None = None, name: str = "") -> None:
        self._succ: dict[Node, dict[Node, None]] = {}
        self._pred: dict[Node, dict[Node, None]] = {}
        self._node_attr: dict[Node, dict[str, Any]] = {}
        self._edge_attr: dict[tuple[Node, Node], dict[str, Any]] = {}
        self.name = name
        if edges is not None:
            self.add_edges_from(edges)

    # ------------------------------------------------------------------ nodes

    def add_node(self, node: Node, **attr: Any) -> None:
        """Add ``node``. Idempotent; attributes merge on repeat calls."""
        if node is None:
            raise ValueError("None cannot be a node")
        if node not in self._succ:
            self._succ[node] = {}
            self._pred[node] = {}
            self._node_attr[node] = {}
        if attr:
            self._node_attr[node].update(attr)

    def add_nodes_from(self, nodes: Iterable[Node], **attr: Any) -> None:
        for n in nodes:
            self.add_node(n, **attr)

    def remove_node(self, node: Node) -> None:
        """Remove ``node`` and every edge incident to it."""
        if node not in self._succ:
            raise NodeNotFound(node)
        for succ in list(self._succ[node]):
            del self._pred[succ][node]
            self._edge_attr.pop((node, succ), None)
        for pred in list(self._pred[node]):
            del self._succ[pred][node]
            self._edge_attr.pop((pred, node), None)
        del self._succ[node]
        del self._pred[node]
        del self._node_attr[node]

    def has_node(self, node: Node) -> bool:
        try:
            return node in self._succ
        except TypeError:          # unhashable
            return False

    # ------------------------------------------------------------------ edges

    def add_edge(self, u: Node, v: Node, **attr: Any) -> None:
        """Add edge ``u -> v``, creating either endpoint if absent.

        Self-loops are permitted at insert time; they are reported as cycles
        by :func:`~ece608.toposort.algos.find_cycle`, which is the layer that
        should decide whether they are an error.
        """
        self.add_node(u)
        self.add_node(v)
        self._succ[u][v] = None
        self._pred[v][u] = None
        if attr:
            self._edge_attr.setdefault((u, v), {}).update(attr)

    def add_edges_from(self, edges: Iterable[Sequence[Node]], **attr: Any) -> None:
        for e in edges:
            if len(e) == 2:
                u, v = e
                self.add_edge(u, v, **attr)
            elif len(e) == 3:
                u, v, data = e
                merged = dict(attr)
                merged.update(data)          # type: ignore[arg-type]
                self.add_edge(u, v, **merged)
            else:
                raise ValueError(f"edge {e!r} must be a 2- or 3-tuple")

    def remove_edge(self, u: Node, v: Node) -> None:
        try:
            del self._succ[u][v]
            del self._pred[v][u]
        except KeyError as err:
            raise NodeNotFound(f"edge {u!r} -> {v!r} is not in the graph") from err
        self._edge_attr.pop((u, v), None)

    def has_edge(self, u: Node, v: Node) -> bool:
        try:
            return v in self._succ[u]
        except (KeyError, TypeError):
            return False

    # ------------------------------------------------------------------ views

    @property
    def nodes(self) -> tuple[Node, ...]:
        """Nodes in insertion order."""
        return tuple(self._succ)

    @property
    def edges(self) -> tuple[tuple[Node, Node], ...]:
        return tuple((u, v) for u, nbrs in self._succ.items() for v in nbrs)

    def successors(self, node: Node) -> Iterator[Node]:
        try:
            return iter(self._succ[node])
        except KeyError as err:
            raise NodeNotFound(node) from err

    def predecessors(self, node: Node) -> Iterator[Node]:
        try:
            return iter(self._pred[node])
        except KeyError as err:
            raise NodeNotFound(node) from err

    def in_degree(self, node: Node) -> int:
        try:
            return len(self._pred[node])
        except KeyError as err:
            raise NodeNotFound(node) from err

    def out_degree(self, node: Node) -> int:
        try:
            return len(self._succ[node])
        except KeyError as err:
            raise NodeNotFound(node) from err

    def node_data(self, node: Node) -> dict[str, Any]:
        try:
            return self._node_attr[node]
        except KeyError as err:
            raise NodeNotFound(node) from err

    def edge_data(self, u: Node, v: Node) -> dict[str, Any]:
        if not self.has_edge(u, v):
            raise NodeNotFound(f"edge {u!r} -> {v!r} is not in the graph")
        return self._edge_attr.setdefault((u, v), {})

    # ------------------------------------------------------------ conversions

    def reverse(self) -> DiGraph:
        """Return a new graph with every edge direction flipped. O(V + E)."""
        g = DiGraph(name=f"reverse of {self.name}" if self.name else "")
        g.add_nodes_from(self._succ)
        for u, v in self.edges:
            g.add_edge(v, u)
        return g

    def copy(self) -> DiGraph:
        g = DiGraph(name=self.name)
        g.add_nodes_from(self._succ)
        for u, v in self.edges:
            g.add_edge(u, v)
        g._node_attr = {n: dict(d) for n, d in self._node_attr.items()}
        g._edge_attr = {e: dict(d) for e, d in self._edge_attr.items()}
        return g

    @classmethod
    def from_adjacency(cls, mapping: dict[Node, Iterable[Node]]) -> DiGraph:
        """Build from ``{node: [successors]}``.

        Keys with no successors still become nodes, which matters: a sink
        that appears only as a key would otherwise vanish from the order.
        """
        g = cls()
        for u, vs in mapping.items():
            g.add_node(u)
            for v in vs:
                g.add_edge(u, v)
        return g

    @classmethod
    def from_matrix(
        cls,
        matrix: Sequence[Sequence[int]],
        labels: Sequence[Node] | None = None,
    ) -> DiGraph:
        """Build from an adjacency matrix where ``matrix[i][j]`` is edge i -> j.

        ``labels`` names the rows; it defaults to ``0..n-1``. Any non-zero
        entry counts as an edge, so weighted matrices are accepted and their
        weights recorded as the ``weight`` edge attribute.
        """
        n = len(matrix)
        for i, row in enumerate(matrix):
            if len(row) != n:
                raise ValueError(
                    f"matrix must be square; row {i} has length {len(row)}, expected {n}"
                )
        if labels is None:
            names: Sequence[Node] = tuple(range(n))
        else:
            if len(labels) != n:
                raise ValueError(f"labels has length {len(labels)}, expected {n}")
            names = tuple(labels)
        g = cls()
        g.add_nodes_from(names)
        for i, row in enumerate(matrix):
            for j, w in enumerate(row):
                if w:
                    g.add_edge(names[i], names[j], weight=w)
        return g

    def to_matrix(self, labels: Sequence[Node] | None = None) -> list[list[int]]:
        """Inverse of :meth:`from_matrix`, using insertion order by default."""
        names = tuple(self._succ) if labels is None else tuple(labels)
        index = {n: i for i, n in enumerate(names)}
        m = [[0] * len(names) for _ in names]
        for u, v in self.edges:
            m[index[u]][index[v]] = 1
        return m

    # ------------------------------------------------------------------ dunder

    def __len__(self) -> int:
        return len(self._succ)

    def __iter__(self) -> Iterator[Node]:
        return iter(self._succ)

    def __contains__(self, node: object) -> bool:
        return self.has_node(node)          # type: ignore[arg-type]

    def __getitem__(self, node: Node) -> Iterator[Node]:
        return self.successors(node)

    def number_of_nodes(self) -> int:
        return len(self._succ)

    def number_of_edges(self) -> int:
        return sum(len(nbrs) for nbrs in self._succ.values())

    def __repr__(self) -> str:
        named = f" {self.name!r}" if self.name else ""
        return f"<DiGraph{named}: {self.number_of_nodes()} nodes, {self.number_of_edges()} edges>"
