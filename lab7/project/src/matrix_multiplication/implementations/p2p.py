"""One-to-one: MPI_Send / MPI_Recv for A strips, B, and C strips."""

from __future__ import annotations

import numpy as np
from mpi4py import MPI

from matrix_multiplication.base import MatrixMultiplyBase
from matrix_multiplication.partition import row_counts


class P2PMatrixMultiply(MatrixMultiplyBase):
    @property
    def name(self) -> str:
        return "p2p"

    def multiply(
        self,
        comm: MPI.Comm,
        a_on_root: np.ndarray | None,
        b_on_root: np.ndarray | None,
    ) -> np.ndarray | None:
        rank = comm.Get_rank()
        size = comm.Get_size()

        if rank == 0:
            assert a_on_root is not None and b_on_root is not None
            a = np.ascontiguousarray(a_on_root, dtype=np.float64)
            b = np.ascontiguousarray(b_on_root, dtype=np.float64)
            n = a.shape[0]
            assert a.shape == (n, n) and b.shape == (n, n)
        else:
            a = np.empty((0, 0), dtype=np.float64)
            b = np.empty((0, 0), dtype=np.float64)
            n = 0

        if size == 1:
            if rank == 0:
                assert a_on_root is not None and b_on_root is not None
                a = np.ascontiguousarray(a_on_root, dtype=np.float64)
                b = np.ascontiguousarray(b_on_root, dtype=np.float64)
                return self.serial_gemm(a, b)
            return None

        if rank != 0:
            n_arr = np.empty(1, dtype=np.int32)
            comm.Recv(n_arr, source=0, tag=8)
            n = int(n_arr[0])

        counts = row_counts(n, size)

        if rank == 0:
            c_full = np.empty((n, n), dtype=np.float64)
            offset = counts[0]
            for dest in range(1, size):
                rows = counts[dest]
                comm.Send(np.int32(n), dest=dest, tag=8)
                comm.Send(np.int32(offset), dest=dest, tag=10)
                comm.Send(np.int32(rows), dest=dest, tag=11)
                if rows > 0:
                    comm.Send(a[offset : offset + rows, :], dest=dest, tag=12)
                    comm.Send(b, dest=dest, tag=13)
                offset += rows

            r0 = counts[0]
            if r0 > 0:
                c_full[0:r0, :] = a[0:r0, :] @ b

            for src in range(1, size):
                rows = counts[src]
                if rows > 0:
                    off = sum(counts[:src])
                    comm.Recv(c_full[off : off + rows, :], source=src, tag=14)
            return c_full

        off = np.empty(1, dtype=np.int32)
        rows_arr = np.empty(1, dtype=np.int32)
        comm.Recv(off, source=0, tag=10)
        comm.Recv(rows_arr, source=0, tag=11)
        rows = int(rows_arr[0])
        if rows > 0:
            a_loc = np.empty((rows, n), dtype=np.float64)
            comm.Recv(a_loc, source=0, tag=12)
            b_loc = np.empty((n, n), dtype=np.float64)
            comm.Recv(b_loc, source=0, tag=13)
            c_loc = a_loc @ b_loc
            comm.Send(c_loc, dest=0, tag=14)
        return None
