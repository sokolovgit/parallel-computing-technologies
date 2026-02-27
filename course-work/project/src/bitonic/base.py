"""Base class for bitonic sort implementations.

Provides shared utilities (power-of-two helpers, timed sort wrapper)
used by both sequential and parallel variants.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SortResult:
    """Holds the sorted array and elapsed wall-clock time."""

    data: NDArray[np.int64]
    elapsed: float


class BitonicSorter:
    """Base class for bitonic sort variants.

    Provides power-of-two padding and a timed sort wrapper; subclasses
    implement the actual sort (sequential or parallel).
    """

    @staticmethod
    def _next_power_of_two(n: int) -> int:
        if n <= 0:
            return 1
        p = 1
        while p < n:
            p <<= 1
        return p

    def _prepare_padded(self, arr: NDArray[np.int64]) -> tuple[NDArray[np.int64], int]:
        """Pad to next power of two with sentinels; return (padded, original_n)."""
        n = len(arr)
        padded_n = self._next_power_of_two(n)
        if padded_n > n:
            sentinel = int(arr.max()) + 1
            padded = np.concatenate(
                [arr, np.full(padded_n - n, sentinel, dtype=np.int64)]
            )
        else:
            padded = arr.copy()
        return padded, n

    def sort(
        self,
        arr: NDArray[np.int64] | list[int],
        ascending: bool = True,
    ) -> NDArray[np.int64]:
        """Sort *arr* and return a new sorted numpy array."""
        raise NotImplementedError

    def sort_timed(
        self,
        arr: NDArray[np.int64] | list[int],
        ascending: bool = True,
    ) -> SortResult:
        """Sort and return a ``SortResult`` with elapsed time."""
        start = time.perf_counter()
        data = self.sort(arr, ascending)
        elapsed = time.perf_counter() - start
        return SortResult(data=data, elapsed=elapsed)
