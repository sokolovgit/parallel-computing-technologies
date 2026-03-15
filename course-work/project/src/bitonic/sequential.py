"""Sequential bitonic sort — iterative implementation.

Complexity: O(n log^2 n). Pure Python on list[int]; no Numba, no NumPy.
Uses the classic iterative comparator network: for block sizes k = 2, 4, ..., n,
merge steps with stride j = k/2, k/4, ..., 1; partner index is i XOR j.

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

from collections.abc import Sequence

from bitonic.base import BitonicSorter


def _bitonic_sort_iterative(arr: list[int], n: int) -> None:
    """Sort arr[0:n] in-place (ascending). n must be a power of 2."""
    if n <= 1:
        return
    k = 2
    while k <= n:
        j = k >> 1
        while j >= 1:
            for i in range(n):
                partner = i ^ j
                if partner <= i:
                    continue
                # (i & k) == 0 → ascending segment; else descending segment
                want_asc = (i & k) == 0
                ai, ap = arr[i], arr[partner]
                if (ai > ap) == want_asc:
                    arr[i], arr[partner] = ap, ai
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
        _bitonic_sort_iterative(padded, len(padded))

        result = padded[:n]
        if not ascending:
            result = result[::-1]
        return result
