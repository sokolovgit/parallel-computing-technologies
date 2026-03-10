"""Parallel bitonic sort using multiprocessing with shared memory.

Design (aligned with technical requirements):

- Process model: fixed process pool (created once), no dynamic process creation.
- Data sharing: multiprocessing.shared_memory + ctypes int64 view; zero-copy, no locks.
- Work distribution: static partitioning by index range (start, end); each worker
  receives one chunk and computes all compare-swap pairs for that chunk locally.
- Synchronization: one barrier per stride via pool.map() so all workers
  finish each stride before the next; required for shared-memory visibility.
  No locks (each (i, j) pair unique per stride).
- Memory: O(n) total; no per-stride array duplication; no O(n) task lists.
- Parallelization unit: (start_index, end_index, stride, size); one map per stride.

Algorithm structure:
  for size in 2, 4, 8, ..., n:
      for stride in size/2, ..., 1:
          parallel compare-swap  (barrier between strides)

Complexity: work O(n log² n), parallel time T_p ≈ (n log² n)/p + O(log² n),
            parallel depth O(log² n).

References:
    https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf
    https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html
"""

from __future__ import annotations

import atexit
import ctypes
import gc
import multiprocessing as mp
from collections.abc import Sequence
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory

from bitonic.base import BitonicSorter


@dataclass(frozen=True)
class _StrideTask:
    """One chunk of work for a single stride (one barrier per stride)."""

    start: int
    end: int
    stride: int
    size: int


# ── Pool-worker state (initialised once per worker process) ───────────

_w_shm: SharedMemory | None = None
_w_arr: ctypes.Array[ctypes.c_int64] | None = None


def _bitonic_stride_core(
    arr: ctypes.Array[ctypes.c_int64],
    start: int,
    end: int,
    stride: int,
    size: int,
) -> None:
    """One compare-swap stride over [start, end). Plain Python."""
    for i in range(start, end):
        partner = i ^ stride
        if partner > i:
            vi, vp = arr[i], arr[partner]
            ascending = (i & size) == 0
            if ascending:
                if vi > vp:
                    arr[i], arr[partner] = vp, vi
            else:
                if vi < vp:
                    arr[i], arr[partner] = vp, vi


def _pool_init(shm_name: str, n: int) -> None:
    """Attach the worker to the shared-memory block (once per process)."""
    global _w_shm, _w_arr  # noqa: PLW0603
    _w_shm = SharedMemory(name=shm_name, create=False)
    assert _w_shm.buf is not None
    _w_arr = (ctypes.c_int64 * n).from_buffer(_w_shm.buf)

    def _release_before_exit() -> None:
        """Release ctypes view so SharedMemory can close when worker process exits."""
        global _w_arr, _w_shm  # noqa: PLW0603
        _w_arr = None
        gc.collect()
        _w_shm = None

    atexit.register(_release_before_exit)


def _pool_worker(task: _StrideTask) -> None:
    """Run one compare-swap stride on indices [task.start, task.end)."""
    assert _w_arr is not None
    _bitonic_stride_core(
        _w_arr,
        task.start,
        task.end,
        task.stride,
        task.size,
    )


class ParallelBitonicSorter(BitonicSorter):
    """Iterative bitonic sort with shared memory and static process pool."""

    def __init__(self, num_processes: int | None = None) -> None:
        self._num_processes = num_processes or mp.cpu_count() or 4

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
        padded_n = len(padded)

        self._sort_parallel(padded, padded_n)

        result = padded[:n]
        if not ascending:
            result = result[::-1]
        return result

    def _sort_parallel(self, padded: list[int], padded_n: int) -> None:
        """Shared memory (ctypes view), fixed pool; one barrier per stride."""
        nbytes = padded_n * ctypes.sizeof(ctypes.c_int64)
        shm = SharedMemory(create=True, size=nbytes)
        try:
            assert shm.buf is not None
            shared_arr = (ctypes.c_int64 * padded_n).from_buffer(shm.buf)
            for i, v in enumerate(padded):
                shared_arr[i] = v

            chunk_size = max(1, padded_n // self._num_processes)
            with mp.Pool(
                self._num_processes,
                initializer=_pool_init,
                initargs=(shm.name, padded_n),
            ) as pool:
                k = 2
                while k <= padded_n:
                    stride = k >> 1
                    while stride > 0:
                        tasks = [
                            _StrideTask(
                                start=s,
                                end=min(s + chunk_size, padded_n),
                                stride=stride,
                                size=k,
                            )
                            for s in range(0, padded_n, chunk_size)
                        ]
                        pool.map(_pool_worker, tasks)
                        stride >>= 1
                    k <<= 1

            for i in range(padded_n):
                padded[i] = shared_arr[i]
            # Release ctypes view so SharedMemory can be closed (no exported pointers).
            del shared_arr
        finally:
            shm.close()
            shm.unlink()
