"""Sequential bitonic sort — iterative Numba JIT (XOR-based) implementation.

Complexity: O(n log^2 n). Uses scalar loops and in-place compare-swap only;
no per-iteration temporary arrays, so compute-bound rather than memory-bound.

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

import numpy as np
from numba import njit
from numpy.typing import NDArray

from bitonic.base import BitonicSorter


@njit
def _bitonic_sort_core(arr: np.ndarray) -> None:
    """In-place iterative (XOR-based) bitonic sort"""
    n = arr.shape[0]
    k = 2
    while k <= n:
        j = k >> 1
        while j > 0:
            for i in range(n):
                partner = i ^ j
                if partner > i:
                    vi, vp = arr[i], arr[partner]
                    ascending = (i & k) == 0
                    if ascending:
                        if vi > vp:
                            arr[i], arr[partner] = vp, vi
                    else:
                        if vi < vp:
                            arr[i], arr[partner] = vp, vi
            j >>= 1
        k <<= 1


def _bitonic_sort_inplace(arr: NDArray[np.int64]) -> None:
    """Run Numba JIT bitonic sort in-place on a int64 array."""
    _bitonic_sort_core(arr)


class SequentialBitonicSorter(BitonicSorter):
    """Iterative bitonic sort (Numba JIT), single process, memory-efficient."""

    def sort(
        self,
        arr: NDArray[np.int64] | list[int],
        ascending: bool = True,
    ) -> NDArray[np.int64]:
        if isinstance(arr, list):
            arr = np.asarray(arr, dtype=np.int64)

        n = len(arr)
        if n <= 1:
            return arr.copy()

        padded, n = self._prepare_padded(arr)
        _bitonic_sort_inplace(padded)

        result = padded[:n].copy()
        if not ascending:
            result = result[::-1].copy()
        return result
