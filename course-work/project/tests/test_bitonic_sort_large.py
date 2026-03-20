import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bitonic import ParallelBitonicSorter, SequentialBitonicSorter


def _make_large_array(size: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(-1_000_000, 1_000_000) for _ in range(size)]


@pytest.mark.slow
class TestLargeSequentialBitonicSorter:
    @pytest.mark.parametrize("size", [524_288, 1_000_000])
    def test_large_random_arrays(self, size):
        arr = _make_large_array(size, seed=size)
        result = SequentialBitonicSorter().sort(arr)
        assert result == sorted(arr)


@pytest.mark.slow
class TestLargeParallelBitonicSorter:
    @pytest.mark.parametrize("size", [524_288, 1_000_000])
    def test_large_random_arrays(self, size):
        arr = _make_large_array(size, seed=size + 1)
        result = ParallelBitonicSorter(num_processes=4).sort(arr)
        assert result == sorted(arr)
