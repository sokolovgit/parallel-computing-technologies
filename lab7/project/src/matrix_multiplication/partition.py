from __future__ import annotations


def row_counts(n_rows: int, n_procs: int) -> list[int]:
    """Rows per rank (block distribution)."""
    if n_procs <= 0:
        raise ValueError("n_procs must be positive")
    base = n_rows // n_procs
    rem = n_rows % n_procs
    return [base + (1 if i < rem else 0) for i in range(n_procs)]


def scatter_counts_and_displs(n: int, size: int) -> tuple[list[int], list[int]]:
    """Element counts and displacements for row-major flattened A (N*N elements)."""
    rows = row_counts(n, size)
    counts = [r * n for r in rows]
    displs: list[int] = []
    acc = 0
    for c in counts:
        displs.append(acc)
        acc += c
    return counts, displs
