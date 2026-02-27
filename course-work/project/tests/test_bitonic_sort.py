"""Correctness tests for sequential and parallel bitonic sort implementations."""

import random
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bitonic import ParallelBitonicSorter, SequentialBitonicSorter

# ---------------------------------------------------------------------------
# Sequential tests
# ---------------------------------------------------------------------------


class TestSequentialBitonicSorter:
    def setup_method(self):
        self.sorter = SequentialBitonicSorter()

    def test_empty(self):
        result = self.sorter.sort(np.array([], dtype=np.int64))
        assert len(result) == 0

    def test_single_element(self):
        assert list(self.sorter.sort([42])) == [42]

    def test_two_elements_sorted(self):
        assert list(self.sorter.sort([1, 2])) == [1, 2]

    def test_two_elements_reversed(self):
        assert list(self.sorter.sort([5, 3])) == [3, 5]

    def test_power_of_two_length(self):
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_non_power_of_two_length(self):
        arr = [5, 3, 8, 1, 9]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_already_sorted(self):
        arr = list(range(16))
        assert list(self.sorter.sort(arr)) == arr

    def test_reverse_sorted(self):
        arr = list(range(16, 0, -1))
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_all_duplicates(self):
        arr = [7] * 8
        assert list(self.sorter.sort(arr)) == arr

    def test_with_duplicates(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_negative_numbers(self):
        arr = [-5, 3, -1, 8, 0, -3, 7, 2]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_descending_order(self):
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(self.sorter.sort(arr, ascending=False)) == sorted(arr, reverse=True)

    def test_large_random(self):
        random.seed(42)
        arr = [random.randint(-10000, 10000) for _ in range(1024)]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_sort_timed(self):
        arr = [4, 2, 7, 1]
        result = self.sorter.sort_timed(arr)
        assert list(result.data) == sorted(arr)
        assert result.elapsed >= 0

    def test_numpy_input(self):
        arr = np.array([10, 30, 11, 20], dtype=np.int64)
        result = self.sorter.sort(arr)
        assert isinstance(result, np.ndarray)
        assert list(result) == [10, 11, 20, 30]


# ---------------------------------------------------------------------------
# Parallel tests
# ---------------------------------------------------------------------------


class TestParallelBitonicSorter:
    def setup_method(self):
        self.sorter = ParallelBitonicSorter(num_processes=2)

    def test_empty(self):
        result = self.sorter.sort(np.array([], dtype=np.int64))
        assert len(result) == 0

    def test_single_element(self):
        assert list(self.sorter.sort([42])) == [42]

    def test_two_elements_sorted(self):
        assert list(self.sorter.sort([1, 2])) == [1, 2]

    def test_two_elements_reversed(self):
        assert list(self.sorter.sort([5, 3])) == [3, 5]

    def test_power_of_two_length(self):
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_non_power_of_two_length(self):
        arr = [5, 3, 8, 1, 9]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_already_sorted(self):
        arr = list(range(16))
        assert list(self.sorter.sort(arr)) == arr

    def test_reverse_sorted(self):
        arr = list(range(16, 0, -1))
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_all_duplicates(self):
        arr = [7] * 8
        assert list(self.sorter.sort(arr)) == arr

    def test_with_duplicates(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_negative_numbers(self):
        arr = [-5, 3, -1, 8, 0, -3, 7, 2]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_single_process(self):
        sorter = ParallelBitonicSorter(num_processes=1)
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(sorter.sort(arr)) == sorted(arr)

    def test_four_processes(self):
        sorter = ParallelBitonicSorter(num_processes=4)
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(sorter.sort(arr)) == sorted(arr)

    def test_large_random(self):
        random.seed(42)
        arr = [random.randint(-10000, 10000) for _ in range(1024)]
        sorter = ParallelBitonicSorter(num_processes=4)
        assert list(sorter.sort(arr)) == sorted(arr)

    def test_sort_timed(self):
        arr = [4, 2, 7, 1]
        result = self.sorter.sort_timed(arr)
        assert list(result.data) == sorted(arr)
        assert result.elapsed >= 0

    def test_numpy_input(self):
        arr = np.array([10, 30, 11, 20], dtype=np.int64)
        result = self.sorter.sort(arr)
        assert isinstance(result, np.ndarray)
        assert list(result) == [10, 11, 20, 30]


# ---------------------------------------------------------------------------
# Cross-implementation consistency
# ---------------------------------------------------------------------------


class TestCrossImplementation:
    @pytest.mark.parametrize("size", [8, 16, 32, 64, 128])
    def test_sequential_matches_parallel(self, size):
        random.seed(size)
        arr = [random.randint(-1000, 1000) for _ in range(size)]
        seq_result = list(SequentialBitonicSorter().sort(arr))
        par_result = list(ParallelBitonicSorter(num_processes=2).sort(arr))
        assert seq_result == par_result == sorted(arr)
