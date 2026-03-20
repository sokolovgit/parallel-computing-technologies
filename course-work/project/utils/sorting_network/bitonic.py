from __future__ import annotations

from collections.abc import Iterator

from .comparator import Comparator
from .network import ComparisonNetwork


def bitonic_comparators(n: int) -> Iterator[Comparator]:
    if n <= 1 or (n & (n - 1)) != 0:
        raise ValueError("n must be a power of two greater than 1")
    k = 2
    while k <= n:
        j = k >> 1
        while j >= 1:
            for i in range(n):
                partner = i ^ j
                if partner <= i:
                    continue
                yield Comparator(i, partner)
            j >>= 1
        k <<= 1


def bitonic_stages(n: int) -> list[tuple[int, int, list[Comparator]]]:
    """Return [(k, j, comparators), ...] so the diagram can show algorithm steps."""
    if n <= 1 or (n & (n - 1)) != 0:
        raise ValueError("n must be a power of two greater than 1")
    stages: list[tuple[int, int, list[Comparator]]] = []
    k = 2
    while k <= n:
        j = k >> 1
        while j >= 1:
            comps: list[Comparator] = []
            for i in range(n):
                partner = i ^ j
                if partner <= i:
                    continue
                comps.append(Comparator(i, partner))
            stages.append((k, j, comps))
            j >>= 1
        k <<= 1
    return stages


def build_bitonic_network(n: int) -> ComparisonNetwork:
    net = ComparisonNetwork()
    for c in bitonic_comparators(n):
        net.append(c)
    return net


def make_chunks(n: int, num_processes: int) -> list[tuple[int, int]]:
    """Same as parallel._make_chunks: (start, end) per process covering [0, n)."""
    chunk_size = max(1, n // num_processes)
    chunks: list[tuple[int, int]] = []
    for p in range(num_processes):
        start = p * chunk_size
        end = n if p == num_processes - 1 else (p + 1) * chunk_size
        chunks.append((start, end))
    return chunks


def process_for_index(i: int, chunks: list[tuple[int, int]]) -> int:
    """Process that owns index i (the one that runs compare-swap for i)."""
    for p, (start, end) in enumerate(chunks):
        if start <= i < end:
            return p
    return 0
