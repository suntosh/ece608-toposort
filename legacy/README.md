# Legacy — the original ECE608 upload

Kept for provenance. **Nothing here is imported by the package**; it is not on
`sys.path` and is excluded from the wheel.

## What is here

| File | Note |
|------|------|
| `original-README.md` | The original two-line README. |
| `original-pyproject.toml` | Declared `dependencies = []` while the code imported `networkx`; declared MIT while `LICENSE` said BSD-2-Clause. |
| `original-algos.py` | The DFS/BFS entry points. Both were stubs that printed a string and returned 0. |
| `original-Exceptions.py` | Exception classes. Named `ECE608_GraphException`; every import site asked for `ECE608GraphException`. |
| `original-LICENSE-BSD2` | The original BSD 2-Clause file, contradicting the MIT declared in `pyproject.toml` and in every SPDX header. |

## What is deliberately *not* here

The original `Graph.py`, `Views.py`, `decorator.py`, and `graphviz.py` were
copied from [NetworkX](https://github.com/networkx/networkx), which is
**BSD-3-Clause** and requires its copyright notice to be carried with any
redistribution. They were shipped here under an MIT declaration with no
notice.

Rather than vendor them correctly, they are dropped: the current package
reimplements what it needs in ~170 lines with no third-party code, so the
obligation does not arise. That is the cleaner resolution — and it is why the
package now has zero runtime dependencies.

If you ever do want NetworkX's graph machinery, depend on `networkx` rather
than copying it.

## Why the original did not run

Verified against the uploaded archive:

- `Graph.py:1` — `from copy import depcopy` (typo) → `ImportError`
- `Views.py:2`, `decorator.py:6` — `from Exceptions import ...`, a Python 2
  implicit relative import → `ModuleNotFoundError` on Python 3
- `graphviz.py:68` — C-style `/* ... */` comment block → `SyntaxError`
- 46 undefined names across the package, including `nx` (11 sites),
  `NetworkXError` (7), `cached_property` (4), `_CachedPropertyResetterAdj`,
  `NodeView`, `EdgeView`, `convert`
- `Graph.to_undirected` calls `self.to_undirected_class()`, never defined
- `Util.py` and `matrix2graphs.py` were empty
- No topological sort anywhere: zero matches for `kahn`, `topolog`, `in_degree`
