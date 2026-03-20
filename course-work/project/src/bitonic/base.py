from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SortResult:
    data: list[int]
    elapsed: float


class BitonicSorter:
    @staticmethod
    def _next_power_of_two(n: int) -> int:
        if n <= 0:
            return 1
        p = 1
        while p < n:
            p <<= 1
        return p

    def _prepare_padded(self, arr: list[int]) -> tuple[list[int], int]:
        n = len(arr)
        if n == 0:
            return [], 0
        padded_n = self._next_power_of_two(n)
        if padded_n > n:
            sentinel = max(arr) + 1
            padded = list(arr) + [sentinel] * (padded_n - n)
        else:
            padded = list(arr)
        return padded, n

    def sort(
        self,
        arr: Sequence[int] | list[int],
        ascending: bool = True,
    ) -> list[int]:
        raise NotImplementedError

    def sort_timed(
        self,
        arr: Sequence[int] | list[int],
        ascending: bool = True,
    ) -> SortResult:
        start = time.perf_counter()
        data = self.sort(arr, ascending)
        elapsed = time.perf_counter() - start
        return SortResult(data=data, elapsed=elapsed)
