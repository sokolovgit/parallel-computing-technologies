"""Sequential bitonic sort — iterative implementation.

Complexity: O(n log^2 n). Pure Python; no Numba, no NumPy.
Uses the classic iterative comparator network: for block sizes k = 2, 4, ..., n,
merge steps with stride j = k/2, k/4, ..., 1; partner index is i XOR j.

Optimizations (no NumPy/Numba): array.array('q') for compact storage and better
cache behavior; single local reference in the inner loop to reduce lookups.

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

from array import array
from collections.abc import Sequence

from bitonic.base import BitonicSorter


def _bitonic_sort_iterative(buf: array | list[int], n: int) -> None:
    """Sort buf[0:n] in-place (ascending). n must be a power of 2."""
    if n <= 1:
        return

    k = 2
    while k <= n:
        j = k >> 1
        while j >= 1:
            a = buf
            for i in range(n):
                partner = i ^ j
                if partner <= i:
                    continue
                want_asc = (i & k) == 0
                vi, vp = a[i], a[partner]
                if (vi > vp) == want_asc:
                    a[i], a[partner] = vp, vi
            j >>= 1
        k <<= 1


class SequentialBitonicSorter(BitonicSorter):
    """Iterative bitonic sort on list[int], single process."""

    def sort(
        self,
        arr: Sequence[int] | list[int],
        ascending: bool = True,
    ) -> list[int]:
        if not isinstance(arr, list):
            arr = list(arr)

        n = len(arr)
        if n <= 1:
            return arr

        padded, n = self._prepare_padded(arr)
        work = array("q", padded)

        _bitonic_sort_iterative(work, len(work))

        result = list(work[:n])
        if not ascending:
            result = result[::-1]

        return result
