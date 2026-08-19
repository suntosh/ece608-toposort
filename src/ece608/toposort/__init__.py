# SPDX-FileCopyrightText: 2022-present Santosh Ahuja <ahuja28@purdue.edu>
# SPDX-License-Identifier: MIT
"""Topological sorting of directed graphs — Kahn's algorithm and DFS.

Written for ECE 608 (Computational Models and Methods, Purdue). No runtime
dependencies; the graph container is part of the package.

    >>> from ece608.toposort import DiGraph, kahn, dfs_topological_sort
    >>> g = DiGraph([("shirt", "tie"), ("tie", "jacket"), ("shirt", "belt")])
    >>> kahn(g)
    ['shirt', 'tie', 'belt', 'jacket']
    >>> dfs_topological_sort(g)
    ['shirt', 'belt', 'tie', 'jacket']

Both are valid: a DAG usually admits many topological orders. Use
:func:`is_topological_order` to check one.
"""

from .__about__ import __version__
from .algos import (
    dfs_topological_sort,
    find_cycle,
    is_dag,
    is_topological_order,
    kahn,
    layers,
    longest_path_length,
)
from .exceptions import CycleError, GraphError, NodeNotFound
from .graph import DiGraph

__all__ = [
    "CycleError",
    "DiGraph",
    "GraphError",
    "NodeNotFound",
    "__version__",
    "dfs_topological_sort",
    "find_cycle",
    "is_dag",
    "is_topological_order",
    "kahn",
    "layers",
    "longest_path_length",
]
