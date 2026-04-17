"""Scatterv + Bcast + Allgatherv."""

from __future__ import annotations

import numpy as np
from mpi4py import MPI

from matrix_multiplication.base import MatrixMultiplyBase
from matrix_multiplication.partition import row_counts, scatter_counts_and_displs


class CollectiveAllgatherv(MatrixMultiplyBase):
    @property
    def name(self) -> str:
        return "allgatherv"

    def multiply(
        self,
        comm: MPI.Comm,
        a_on_root: np.ndarray | None,
        b_on_root: np.ndarray | None,
    ) -> np.ndarray | None:
        rank = comm.Get_rank()
        size = comm.Get_size()

        n_root: int | None = None
        if rank == 0:
            assert a_on_root is not None and b_on_root is not None
            a = np.ascontiguousarray(a_on_root, dtype=np.float64)
            b = np.ascontiguousarray(b_on_root, dtype=np.float64)
            n_root = a.shape[0]
        n = self.bcast_int_n(comm, rank, n_root)

        if size == 1:
            if rank == 0:
                assert a_on_root is not None and b_on_root is not None
                a = np.ascontiguousarray(a_on_root, dtype=np.float64)
                b = np.ascontiguousarray(b_on_root, dtype=np.float64)
                return self.serial_gemm(a, b)
            return None

        counts = row_counts(n, size)
        scounts, displs = scatter_counts_and_displs(n, size)

        my_rows = counts[rank]
        recv_a = np.empty(max(my_rows * n, 0), dtype=np.float64)
        if rank == 0:
            flat_a = np.ascontiguousarray(a.ravel())
            comm.Scatterv([flat_a, scounts, displs, MPI.DOUBLE], recv_a, root=0)
        else:
            comm.Scatterv(None, recv_a, root=0)

        b_loc = np.empty((n, n), dtype=np.float64)
        if rank == 0:
            b_loc[:] = b
        comm.Bcast(b_loc, root=0)

        if my_rows > 0:
            a_loc = recv_a[: my_rows * n].reshape(my_rows, n)
            c_loc = (a_loc @ b_loc).ravel()
        else:
            c_loc = np.empty(0, dtype=np.float64)

        recv_c = np.empty(n * n, dtype=np.float64)
        comm.Allgatherv(c_loc, [recv_c, scounts, displs, MPI.DOUBLE])

        return recv_c.reshape(n, n) if rank == 0 else None
