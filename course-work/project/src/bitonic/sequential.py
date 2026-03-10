"""Sequential bitonic sort — simple recursive implementation.

Complexity: O(n log^2 n). Pure Python on list[int]; no Numba, no NumPy.

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

from collections.abc import Sequence

from bitonic.base import BitonicSorter


def _bitonic_merge(arr: list[int], low: int, n: int, ascending: bool) -> None:
    """Merge bitonic sequence arr[low:low+n] into sorted order (in-place)."""
    if n <= 1:
        return
    half = n >> 1
    for i in range(half):
        a, b = low + i, low + half + i
        if (arr[a] > arr[b]) == ascending:
            arr[a], arr[b] = arr[b], arr[a]
    _bitonic_merge(arr, low, half, ascending)
    _bitonic_merge(arr, low + half, half, ascending)


def _bitonic_sort_range(arr: list[int], low: int, n: int, ascending: bool) -> None:
    """Sort arr[low:low+n] into a bitonic sequence and then merge to sorted."""
    if n <= 1:
        return
    half = n >> 1
    _bitonic_sort_range(arr, low, half, True)
    _bitonic_sort_range(arr, low + half, half, False)
    _bitonic_merge(arr, low, n, ascending)


class SequentialBitonicSorter(BitonicSorter):
    """Recursive bitonic sort on list[int], single process."""

    def sort(
        self,
        arr: Sequence[int] | list[int],
        ascending: bool = True,
    ) -> list[int]:
        arr = list(arr)
        n = len(arr)
        if n <= 1:
            return arr

        padded, n = self._prepare_padded(arr)
        _bitonic_sort_range(padded, 0, len(padded), True)

        result = padded[:n]
        if not ascending:
            result = result[::-1]
        return result
