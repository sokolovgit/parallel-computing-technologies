"""Sequential bitonic sort — iterative numpy (XOR-based) implementation.

Complexity: O(n log^2 n).

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from bitonic.base import BitonicSorter


def _bitonic_sort_numpy_inplace(arr: NDArray[np.int64]) -> None:
    """In-place iterative (XOR-based) bitonic sort — sequential implementation."""
    n = len(arr)
    k = 2
    while k <= n:
        j = k >> 1
        while j > 0:
            indices = np.arange(n, dtype=np.intp)
            partners = indices ^ j
            mask = partners > indices
            i_idx = indices[mask]
            p_idx = partners[mask]
            vals_i = arr[i_idx].copy()
            vals_p = arr[p_idx].copy()
            ascending = (i_idx & k) == 0
            swap = np.where(ascending, vals_i > vals_p, vals_i < vals_p)
            arr[i_idx] = np.where(swap, vals_p, vals_i)
            arr[p_idx] = np.where(swap, vals_i, vals_p)
            j >>= 1
        k <<= 1


class SequentialBitonicSorter(BitonicSorter):
    """Iterative numpy bitonic sort, single process."""

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
        _bitonic_sort_numpy_inplace(padded)

        result = padded[:n].copy()
        if not ascending:
            result = result[::-1].copy()
        return result
