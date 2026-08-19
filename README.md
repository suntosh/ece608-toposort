# ece608-toposort

Topological ordering of directed graphs by two independent routes — **Kahn's
algorithm** and **DFS reverse postorder** — with cycle detection that tells you
*which* nodes cycle, not merely that one exists.

Written for ECE 608 (Computational Models and Methods, Purdue).

**No runtime dependencies.** The graph container is part of the package, in
about 170 lines. That is a deliberate choice for a teaching implementation: the
point is to show the algorithms, and a dependency on `networkx` would mean the
interesting parts live in someone else's repository.

```python
from ece608.toposort import DiGraph, kahn, dfs_topological_sort, layers

g = DiGraph([("shirt", "tie"), ("tie", "jacket"), ("shirt", "belt")])

kahn(g)                    # ['shirt', 'tie', 'belt', 'jacket']
dfs_topological_sort(g)    # ['shirt', 'belt', 'tie', 'jacket']
layers(g)                  # [['shirt'], ['tie', 'belt'], ['jacket']]
```

Both orders are correct. A DAG generally admits many topological orders; use
`is_topological_order(g, order)` to check one rather than comparing against a
fixed sequence.

## Install

```bash
git clone https://github.com/suntosh/ece608-toposort
cd ece608-toposort
pip install -e ".[dev]"
pytest
```

Requires Python 3.9+.

## The two algorithms

| | `kahn` | `dfs_topological_sort` |
|---|---|---|
| Method | peel in-degree-zero nodes off a frontier | reverse postorder of a DFS forest |
| Time | O(V + E) | O(V + E) |
| Auxiliary space | O(V) | O(V) |
| Recursion | none | none — explicit stack |
| Deterministic tie-break | yes, via `key=` | insertion order only |
| Extends toward | incremental / streaming updates | SCC, dominators, cycle structure |

**Kahn** maintains a live in-degree count and drains a frontier. Its state is a
partially consumed graph, which makes it the natural base for incremental work
— if you later add an edge and want to know whether the order is still valid,
this is the one to extend. The `key=` argument makes the output
*content-defined*: the same graph built in a different insertion order yields
the same list, at O(V log V) instead of O(V + E). That matters when the order
feeds a build system or a test fixture.

**DFS** produces reverse postorder, which is the numbering that
strongly-connected-components and dominator algorithms are built on. If the
next thing you need is graph *structure* rather than just an order, start here.

Both are iterative. A recursive DFS is shorter to write but dies on a chain of
about 1000 nodes under CPython's default recursion limit; `test_algos.py`
sorts a 20,000-node chain to hold that line.

### Cycles

Neither sort returns a partial result on a cyclic graph — both raise
`CycleError`, which carries the offending cycle:

```python
>>> from ece608.toposort import DiGraph, kahn, CycleError
>>> try:
...     kahn(DiGraph([("a", "b"), ("b", "c"), ("c", "a")]))
... except CycleError as e:
...     e.cycle
['a', 'b', 'c', 'a']
```

This is the difference between an error a caller can act on and one they can
only report. `find_cycle(g)` and `is_dag(g)` are available separately when you
want to ask before you sort.

### Layers

`layers(g)` partitions the graph into ranks, where rank *i* holds every node
whose longest incoming path has length *i*. Everything within a layer is
mutually independent, so it is a parallel schedule: layer *i* can begin only
after *i−1*, and can run fully concurrently within itself.
`longest_path_length(g)` is the critical path — the lower bound on sequential
steps.

## API

```
DiGraph(edges=None, name="")
  add_node / add_nodes_from / remove_node / has_node
  add_edge / add_edges_from / remove_edge / has_edge
  nodes / edges / successors / predecessors
  in_degree / out_degree / node_data / edge_data
  reverse / copy / to_matrix
  DiGraph.from_adjacency({node: [successors]})
  DiGraph.from_matrix(matrix, labels=None)

kahn(graph, key=None)              -> list[Node]
dfs_topological_sort(graph)        -> list[Node]
is_topological_order(graph, order) -> bool
find_cycle(graph)                  -> list[Node] | None
is_dag(graph)                      -> bool
layers(graph)                      -> list[list[Node]]
longest_path_length(graph)         -> int
```

Predecessors are mirrored eagerly, so `in_degree` is O(1). That doubles edge
storage and is the reason Kahn's stays O(V + E) rather than O(V·E) — recounting
in-degrees inside the drain loop is the usual way this algorithm silently goes
quadratic.

## Tests

112 tests, 95% line coverage, plus doctests.

```bash
pytest --cov --cov-report=term-missing
pytest --doctest-modules src/ece608/toposort
```

The suite asserts the topological-order *property* over 25 seeded random DAGs
rather than checking golden sequences, and covers the cases that break naive
implementations: isolated sinks that appear only as adjacency keys, self-loops,
a cycle unreachable from any source, disconnected components, duplicate edges,
and the deep chain above.

## Benchmark

`python3 bench/bench_toposort.py` sorts DAGs from 10k to 80k nodes and prints
the growth ratio. Doubling the graph should roughly double the time; a drift
toward 4× means something has gone quadratic.

Measured ratios run about 2.2–2.7× rather than a clean 2.0. That is cache and
dict-growth behaviour at these sizes, not a complexity problem — a quadratic
implementation shows ~4× per doubling.


## License

MIT. See [LICENSE](LICENSE).
