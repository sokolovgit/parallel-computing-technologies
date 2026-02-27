"""Parallel bitonic sort using multiprocessing with shared memory.

Design (aligned with technical requirements):

- Process model: fixed process pool (created once), no dynamic process creation.
- Data sharing: multiprocessing.shared_memory + NumPy view; zero-copy, no locks.
- Work distribution: static partitioning by index range (start, end); each worker
  receives one chunk and computes all compare-swap pairs for that chunk locally.
- Synchronization: one barrier per *size* (not per stride) via pool.map();
  within each size the worker runs all strides locally, reducing IPC from
  O(log² n) to O(log n) map calls. No locks (each (i, j) pair unique).
- Memory: O(n) total; no per-stride array duplication; no O(n) task lists.
- Parallelization unit: (start_index, end_index, size); worker runs all strides
  for that size locally. Minimizes IPC (O(log n) map calls instead of O(log² n)).

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

import multiprocessing as mp
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory

import numpy as np
from numba import njit
from numpy.typing import NDArray

from bitonic.base import BitonicSorter


@dataclass(frozen=True)
class _SizeTask:
    """One chunk of work for a full size (all strides for this size)."""

    start: int
    end: int
    size: int  # k in bitonic: we run all strides from size/2 down to 1


# ── Pool-worker state (initialised once per worker process) ───────────

_w_shm: SharedMemory | None = None
_w_arr: NDArray[np.int64] | None = None


@njit
def _bitonic_stride_core(
    arr: np.ndarray, start: int, end: int, stride: int, size: int
) -> None:
    """One compare-swap stride over [start, end). No temporary arrays."""
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
    _w_arr = np.ndarray(n, dtype=np.int64, buffer=_w_shm.buf)


def _pool_worker(task: _SizeTask) -> None:
    """Run all compare-swap strides for task.size on indices [task.start, task.end).

    Uses scalar loop (Numba) per stride — no per-stride array allocations.
    """
    assert _w_arr is not None
    arr = _w_arr
    start_idx, end_idx = task.start, task.end
    size = task.size

    stride = size >> 1
    while stride > 0:
        _bitonic_stride_core(arr, start_idx, end_idx, stride, size)
        stride >>= 1


class ParallelBitonicSorter(BitonicSorter):
    """Iterative bitonic sort with shared memory and static process pool."""

    def __init__(self, num_processes: int | None = None) -> None:
        self._num_processes = num_processes or mp.cpu_count() or 4

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

        self._sort_parallel(padded)

        result = padded[:n].copy()
        if not ascending:
            result = result[::-1].copy()
        return result

    def _sort_parallel(self, padded: NDArray[np.int64]) -> None:
        """Shared memory, fixed pool; one barrier per size (strides batched)."""
        padded_n = len(padded)

        # Allocate shared memory, copy input
        shm = SharedMemory(create=True, size=padded.nbytes)
        try:
            shared_arr: NDArray[np.int64] = np.ndarray(
                padded.shape, dtype=padded.dtype, buffer=shm.buf
            )
            shared_arr[:] = padded

            chunk_size = max(1, padded_n // self._num_processes)
            with mp.Pool(
                self._num_processes,
                initializer=_pool_init,
                initargs=(shm.name, padded_n),
            ) as pool:
                # One map per size k; worker runs all strides for k (fewer barriers)
                k = 2
                while k <= padded_n:
                    tasks = [
                        _SizeTask(
                            start=s,
                            end=min(s + chunk_size, padded_n),
                            size=k,
                        )
                        for s in range(0, padded_n, chunk_size)
                    ]
                    pool.map(_pool_worker, tasks)
                    k <<= 1

            padded[:] = shared_arr
        finally:
            shm.close()
            shm.unlink()
