from __future__ import annotations

from array import array
from collections.abc import Sequence

from bitonic.base import BitonicSorter


def _bitonic_sort_iterative(arr: array | list[int], n: int) -> None:
    if n <= 1:
        return

    k = 2
    while k <= n:
        j = k >> 1
        while j >= 1:
            a = arr
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
        arr = array("q", padded)

        _bitonic_sort_iterative(arr, len(arr))

        result = list(arr[:n])
        if not ascending:
            result = result[::-1]

        return result
