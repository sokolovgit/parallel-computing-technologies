# ДОДАТОК А. Послідовна та паралельна реалізація бітонічного сортування

У додатку наведено вихідний код пакета `bitonic` без коментарів (файли в проєкті: `course-work/project/src/bitonic/`). Для запуску з каталогу `project` потрібно додати `src` до `PYTHONPATH` або виконувати коди з кореня проєкту, де налаштовано імпорт.

## А.1. `__init__.py`

```python
from bitonic.base import BitonicSorter, SortResult
from bitonic.parallel import ParallelBitonicSorter
from bitonic.sequential import SequentialBitonicSorter

__all__ = [
    "BitonicSorter",
    "ParallelBitonicSorter",
    "SequentialBitonicSorter",
    "SortResult",
]
```

## А.2. `base.py`

```python
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
```

## А.3. `sequential.py`

```python
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
```

## А.4. `parallel.py`

```python
from __future__ import annotations

import atexit
import ctypes
import gc
import multiprocessing as mp
from collections.abc import Sequence
from multiprocessing.shared_memory import SharedMemory

from bitonic.base import BitonicSorter

_w_shm: SharedMemory | None = None
_w_arr: ctypes.Array[ctypes.c_int64] | None = None


def _bitonic_stride_core(
    arr: ctypes.Array[ctypes.c_int64],
    start: int,
    end: int,
    stride: int,
    size: int,
) -> None:
    arr_local = arr
    for i in range(start, end):
        partner = i ^ stride
        if partner <= i:
            continue
        vi = arr_local[i]
        vp = arr_local[partner]
        if (vi > vp) == ((i & size) == 0):
            arr_local[i], arr_local[partner] = vp, vi


def _pool_init(shm_name: str, n: int) -> None:
    global _w_shm, _w_arr
    _w_shm = SharedMemory(name=shm_name, create=False)
    assert _w_shm.buf is not None
    _w_arr = (ctypes.c_int64 * n).from_buffer(_w_shm.buf)

    def _release_before_exit() -> None:
        global _w_arr, _w_shm
        _w_arr = None
        gc.collect()
        _w_shm = None

    atexit.register(_release_before_exit)


def _pool_worker(task: tuple[int, int, int, int]) -> None:
    assert _w_arr is not None
    start, end, stride, size = task
    _bitonic_stride_core(_w_arr, start, end, stride, size)


def _make_chunks(padded_n: int, num_processes: int) -> list[tuple[int, int]]:
    chunk_size = max(1, padded_n // num_processes)
    chunks: list[tuple[int, int]] = []
    for p in range(num_processes):
        start = p * chunk_size
        end = padded_n if p == num_processes - 1 else (p + 1) * chunk_size
        chunks.append((start, end))
    return chunks


class ParallelBitonicSorter(BitonicSorter):
    def __init__(self, num_processes: int | None = None) -> None:
        self._num_processes = num_processes or mp.cpu_count() or 4

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
        padded_n = len(padded)

        self._sort_parallel(padded, padded_n)

        result = padded[:n]
        if not ascending:
            result = result[::-1]
        return result

    def _sort_parallel(self, padded: list[int], padded_n: int) -> None:
        nbytes = padded_n * ctypes.sizeof(ctypes.c_int64)
        shm = SharedMemory(create=True, size=nbytes)
        try:
            assert shm.buf is not None
            shared_arr = (ctypes.c_int64 * padded_n).from_buffer(shm.buf)
            for i, v in enumerate(padded):
                shared_arr[i] = v

            num_workers = min(self._num_processes, padded_n)
            chunks = _make_chunks(padded_n, num_workers)
            pool = mp.Pool(
                num_workers,
                initializer=_pool_init,
                initargs=(shm.name, padded_n),
            )
            try:
                k = 2
                while k <= padded_n:
                    stride = k >> 1
                    while stride > 0:
                        tasks = [(start, end, stride, k) for start, end in chunks]
                        pool.map(_pool_worker, tasks)
                        stride >>= 1
                    k <<= 1
            finally:
                pool.close()
                pool.join()

            padded[:] = shared_arr[:]
            del shared_arr
        finally:
            shm.close()
            shm.unlink()
```
