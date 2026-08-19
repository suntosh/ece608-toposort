#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Empirical check that both sorts are linear in V + E.

    python3 bench/bench_toposort.py

Doubling the graph should roughly double the time. If a change makes the
ratio drift toward 4x, something has become quadratic — most likely an
in-degree recount inside the drain loop.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ece608.toposort import DiGraph, dfs_topological_sort, kahn  # noqa: E402


def build(n: int, avg_out: int, seed: int = 1) -> DiGraph:
    rng = random.Random(seed)
    g = DiGraph()
    g.add_nodes_from(range(n))
    for u in range(n):
        for _ in range(avg_out):
            v = rng.randint(u + 1, n - 1) if u + 1 < n else None
            if v is not None:
                g.add_edge(u, v)
    return g


def main() -> None:
    print(f"{'V':>9} {'E':>10} {'kahn ms':>10} {'dfs ms':>10} {'us/edge':>9}")
    prev = None
    for n in (10_000, 20_000, 40_000, 80_000):
        g = build(n, avg_out=3)
        e = g.number_of_edges()
        t0 = time.perf_counter(); kahn(g);                  t1 = time.perf_counter()
        dfs_topological_sort(g);                            t2 = time.perf_counter()
        k_ms, d_ms = (t1 - t0) * 1e3, (t2 - t1) * 1e3
        print(f"{n:>9,} {e:>10,} {k_ms:>10.1f} {d_ms:>10.1f} {k_ms*1e3/e:>9.3f}")
        if prev:
            print(f"{'':>9} {'':>10} ratio vs previous: {k_ms/prev:>4.2f}x  (linear => ~2.0)")
        prev = k_ms


if __name__ == "__main__":
    main()
