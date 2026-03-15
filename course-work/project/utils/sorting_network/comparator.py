from __future__ import annotations


class Comparator:
    def __init__(self, i1: int, i2: int) -> None:
        if i1 == i2:
            raise ValueError("Comparator inputs must be different")
        self.i1, self.i2 = (i1, i2) if i1 < i2 else (i2, i1)

    def overlaps(self, other: Comparator) -> bool:
        return (
            (self.i1 < other.i1 < self.i2)
            or (self.i1 < other.i2 < self.i2)
            or (other.i1 < self.i1 < other.i2)
            or (other.i1 < self.i2 < other.i2)
        )

    def has_same_input(self, other: Comparator) -> bool:
        return (
            self.i1 == other.i1
            or self.i1 == other.i2
            or self.i2 == other.i1
            or self.i2 == other.i2
        )
