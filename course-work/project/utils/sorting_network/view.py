"""Text/ASCII view of bitonic stages — see the algorithm flow without opening SVG."""

from __future__ import annotations

from .comparator import Comparator


def format_stages(
    stages: list[tuple[int, int, list[Comparator]]],
    n: int,
    title: str | None = None,
) -> str:
    """Human-readable list of stages: k (block size), j (stride), and compare pairs."""
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("")
    lines.append(f"n = {n} wires. Each stage: compare-swap (i, i^j) for stride j.")
    lines.append("")
    for idx, (k, j, comps) in enumerate(stages, 1):
        pairs = " ".join(f"({c.i1},{c.i2})" for c in comps)
        lines.append(f"Stage {idx}: k={k}, j={j}  →  {pairs}")
    return "\n".join(lines)
