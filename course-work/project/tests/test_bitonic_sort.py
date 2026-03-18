"""Correctness tests for sequential and parallel bitonic sort implementations."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bitonic import ParallelBitonicSorter, SequentialBitonicSorter
from bitonic.base import BitonicSorter

# ---------------------------------------------------------------------------
# Sequential tests
# ---------------------------------------------------------------------------


class TestSequentialBitonicSorter:
    def setup_method(self):
        self.sorter = SequentialBitonicSorter()

    def test_empty(self):
        result = self.sorter.sort([])
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

    def test_large_int64_safe(self):
        """Values within int64 range (parallel uses c_int64)."""
        random.seed(123)
        arr = [random.randint(-(10**12), 10**12) for _ in range(64)]
        assert list(self.sorter.sort(arr)) == sorted(arr)

    def test_sort_timed(self):
        arr = [4, 2, 7, 1]
        result = self.sorter.sort_timed(arr)
        assert list(result.data) == sorted(arr)
        assert result.elapsed >= 0

    def test_three_elements(self):
        arr = [3, 1, 2]
        assert list(self.sorter.sort(arr)) == [1, 2, 3]

    def test_input_not_mutated(self):
        arr = [5, 2, 8, 1]
        orig = list(arr)
        self.sorter.sort(arr)
        assert arr == orig


# ---------------------------------------------------------------------------
# Parallel tests
# ---------------------------------------------------------------------------


class TestParallelBitonicSorter:
    def setup_method(self):
        self.sorter = ParallelBitonicSorter(num_processes=2)

    def test_empty(self):
        result = self.sorter.sort([])
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

    def test_more_processes_than_elements(self):
        """Process count > n is clamped; no invalid chunks (start > end)."""
        sorter = ParallelBitonicSorter(num_processes=16)
        arr = [3, 1, 4, 2]
        assert list(sorter.sort(arr)) == sorted(arr)

    def test_descending_order(self):
        arr = [10, 30, 11, 20, 4, 330, 21, 110]
        assert list(self.sorter.sort(arr, ascending=False)) == sorted(arr, reverse=True)

    def test_three_elements(self):
        arr = [3, 1, 2]
        assert list(self.sorter.sort(arr)) == [1, 2, 3]

    def test_input_not_mutated(self):
        arr = [5, 2, 8, 1]
        orig = list(arr)
        self.sorter.sort(arr)
        assert arr == orig

    def test_large_int64_safe(self):
        """Values within int64 range; no sentinel overflow."""
        random.seed(123)
        arr = [random.randint(-(10**12), 10**12) for _ in range(64)]
        assert list(self.sorter.sort(arr)) == sorted(arr)

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


# ---------------------------------------------------------------------------
# Base / padding
# ---------------------------------------------------------------------------


class TestBitonicBase:
    """Tests for power-of-two padding and base behavior."""

    def test_next_power_of_two(self):
        assert BitonicSorter._next_power_of_two(0) == 1
        assert BitonicSorter._next_power_of_two(1) == 1
        assert BitonicSorter._next_power_of_two(2) == 2
        assert BitonicSorter._next_power_of_two(3) == 4
        assert BitonicSorter._next_power_of_two(5) == 8
        assert BitonicSorter._next_power_of_two(9) == 16

    def test_prepare_padded_empty(self):
        sorter = SequentialBitonicSorter()
        padded, n = sorter._prepare_padded([])
        assert padded == []
        assert n == 0

    def test_prepare_padded_power_of_two(self):
        sorter = SequentialBitonicSorter()
        arr = [1, 2, 4, 3]
        padded, n = sorter._prepare_padded(arr)
        assert len(padded) == 4
        assert n == 4
        assert padded == arr

    def test_prepare_padded_non_power_of_two(self):
        sorter = SequentialBitonicSorter()
        arr = [1, 2, 3]
        padded, n = sorter._prepare_padded(arr)
        assert n == 3
        assert len(padded) == 4
        assert padded[:3] == [1, 2, 3]
        assert padded[3] == max(arr) + 1


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

    @pytest.mark.parametrize("size", [5, 7, 11, 16])
    def test_sequential_matches_parallel_non_power_of_two(self, size):
        random.seed(size + 100)
        arr = [random.randint(-1000, 1000) for _ in range(size)]
        seq_result = list(SequentialBitonicSorter().sort(arr))
        par_result = list(ParallelBitonicSorter(num_processes=2).sort(arr))
        assert seq_result == par_result == sorted(arr)

    @pytest.mark.parametrize("size", [8, 16])
    def test_sequential_matches_parallel_descending(self, size):
        random.seed(size + 200)
        arr = [random.randint(-1000, 1000) for _ in range(size)]
        seq_result = list(SequentialBitonicSorter().sort(arr, ascending=False))
        par_result = list(
            ParallelBitonicSorter(num_processes=2).sort(arr, ascending=False)
        )
        expected = sorted(arr, reverse=True)
        assert seq_result == par_result == expected
