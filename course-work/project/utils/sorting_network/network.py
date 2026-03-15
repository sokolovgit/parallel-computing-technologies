from __future__ import annotations

from .comparator import Comparator


class ComparisonNetwork:
    def __init__(self) -> None:
        self.comparators: list[Comparator] = []

    def append(self, c: Comparator) -> None:
        self.comparators.append(c)

    def get_max_input(self) -> int:
        if not self.comparators:
            raise ValueError("Comparison network is empty")
        return max(c.i2 for c in self.comparators)

    def _get_optimized_comparators(self) -> list[Comparator]:
        remaining = self.comparators.copy()
        result: list[Comparator] = []
        while remaining:
            current_depth: list[Comparator] = []
            considered: list[Comparator] = []
            for c in remaining.copy():
                if any(c.has_same_input(d) for d in considered):
                    considered.append(c)
                    continue
                current_depth.append(c)
                remaining.remove(c)
                considered.append(c)
            result.extend(self._optimize_comparator_depth_group(current_depth))
        return result

    @staticmethod
    def _optimize_comparator_depth_group(
        comparators: list[Comparator],
    ) -> list[Comparator]:
        remaining = comparators.copy()
        overlap_count = {
            c: sum(1 for o in remaining if c.overlaps(o)) for c in remaining
        }
        result: list[Comparator] = []
        while remaining:
            min_overlap = min(overlap_count.values())
            candidates = [c for c in remaining if overlap_count[c] == min_overlap]
            if len(candidates) > 1:
                max_range = max(c.i2 - c.i1 for c in candidates)
                candidates = [c for c in candidates if c.i2 - c.i1 == max_range]
            chosen = min(candidates, key=lambda x: x.i1)
            result.append(chosen)
            remaining.remove(chosen)
            del overlap_count[chosen]
        return result
