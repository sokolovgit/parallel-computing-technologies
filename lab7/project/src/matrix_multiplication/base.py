"""Abstract base for parallel C = A @ B implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from mpi4py import MPI


class MatrixMultiplyBase(ABC):
    """Shared contract: full C on rank 0 only; other ranks return None."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Registry key (e.g. ``p2p``)."""

    @abstractmethod
    def multiply(
        self,
        comm: MPI.Comm,
        a_on_root: np.ndarray | None,
        b_on_root: np.ndarray | None,
    ) -> np.ndarray | None:
        """Compute C = A @ B in parallel."""

    @staticmethod
    def serial_gemm(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return a @ b

    @staticmethod
    def bcast_int_n(comm: MPI.Comm, rank: int, n: int | None) -> int:
        """Broadcast matrix order N from root as int32 (all ranks must call)."""
        buf = np.zeros(1, dtype=np.int32)
        if rank == 0:
            assert n is not None
            buf[0] = n
        comm.Bcast(buf, root=0)
        return int(buf[0])
