# SPDX-FileCopyrightText: 2022-present Santosh Ahuja <ahuja28@purdue.edu>
# SPDX-License-Identifier: MIT
"""Exceptions raised by :mod:`ece608.toposort`."""

from __future__ import annotations

__all__ = ["CycleError", "GraphError", "NodeNotFound"]


class GraphError(Exception):
    """Base class for every error raised by this package."""


class NodeNotFound(GraphError, KeyError):
    """Raised when an operation references a node the graph does not contain."""


class CycleError(GraphError):
    """Raised when a topological order is requested for a graph with a cycle.

    The offending cycle is attached so callers can report it rather than
    guessing which edge to remove.
    """

    def __init__(self, cycle: list[object]) -> None:
        self.cycle = list(cycle)
        rendered = " -> ".join(repr(n) for n in self.cycle)
        super().__init__(f"graph is cyclic: {rendered}")
