"""Text/ASCII view of bitonic stages — see the algorithm flow without opening SVG."""

from __future__ import annotations

from .bitonic import make_chunks, process_for_index
from .comparator import Comparator


def format_stages(
    stages: list[tuple[int, int, list[Comparator]]],
    n: int,
    title: str | None = None,
    processes: int | None = None,
) -> str:
    """Human-readable list of stages; if processes set, show which process does which pairs."""
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("")
    lines.append(f"n = {n} wires. Each stage: compare-swap (i, i^j) for stride j.")
    if processes and processes > 0:
        lines.append(f"Parallel: P = {processes} processes (index range [start,end) per process).")
    lines.append("")
    chunks = make_chunks(n, processes) if processes and processes > 0 else None

    for idx, (k, j, comps) in enumerate(stages, 1):
        if chunks:
            by_p: dict[int, list[str]] = {}
            for c in comps:
                p = process_for_index(c.i1, chunks)
                by_p.setdefault(p, []).append(f"({c.i1},{c.i2})")
            parts = [f"P{p} {' '.join(by_p[p])}" for p in range(len(chunks)) if p in by_p]
            lines.append(f"Stage {idx}: k={k}, j={j}  →  {'  |  '.join(parts)}")
        else:
            pairs = " ".join(f"({c.i1},{c.i2})" for c in comps)
            lines.append(f"Stage {idx}: k={k}, j={j}  →  {pairs}")
    return "\n".join(lines)
