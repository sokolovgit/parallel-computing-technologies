from __future__ import annotations

from collections.abc import Iterator

from matrix_multiplication.base import MatrixMultiplyBase
from matrix_multiplication.implementations import (
    CollectiveAllgatherv,
    CollectiveScatterBcastGather,
    P2PDistributeGatherv,
    P2PMatrixMultiply,
)

ALGOS: dict[str, MatrixMultiplyBase] = {
    "p2p": P2PMatrixMultiply(),
    "collective_sbg": CollectiveScatterBcastGather(),
    "p2p_gatherv": P2PDistributeGatherv(),
    "allgatherv": CollectiveAllgatherv(),
}


def iter_algos() -> Iterator[tuple[str, MatrixMultiplyBase]]:
    for k, v in ALGOS.items():
        yield k, v
