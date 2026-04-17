"""P2P distribution; Gatherv for C."""

from __future__ import annotations

import numpy as np
from mpi4py import MPI

from matrix_multiplication.base import MatrixMultiplyBase
from matrix_multiplication.partition import row_counts, scatter_counts_and_displs


class P2PDistributeGatherv(MatrixMultiplyBase):
    @property
    def name(self) -> str:
        return "p2p_gatherv"

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
        else:
            n_arr = np.empty(1, dtype=np.int32)
            comm.Recv(n_arr, source=0, tag=8)
            n = int(n_arr[0])
            a = np.empty((0, 0), dtype=np.float64)
            b = np.empty((0, 0), dtype=np.float64)

        if size == 1:
            if rank == 0:
                assert a_on_root is not None and b_on_root is not None
                a = np.ascontiguousarray(a_on_root, dtype=np.float64)
                b = np.ascontiguousarray(b_on_root, dtype=np.float64)
                return self.serial_gemm(a, b)
            return None

        counts = row_counts(n, size)
        scounts, displs = scatter_counts_and_displs(n, size)

        if rank == 0:
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

        my_rows = counts[rank]
        if rank == 0:
            if my_rows > 0:
                a_loc = a[0:my_rows, :].copy()
            else:
                a_loc = np.empty((0, n), dtype=np.float64)
            b_loc = b.copy()
        else:
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
            else:
                a_loc = np.empty((0, n), dtype=np.float64)
                b_loc = np.empty((0, 0), dtype=np.float64)

        if my_rows > 0:
            c_loc = (a_loc @ b_loc).ravel()
        else:
            c_loc = np.empty(0, dtype=np.float64)

        recv_c = np.empty(n * n, dtype=np.float64) if rank == 0 else None
        if rank == 0:
            comm.Gatherv(c_loc, [recv_c, scounts, displs, MPI.DOUBLE], root=0)
            assert recv_c is not None
            return recv_c.reshape(n, n)
        comm.Gatherv(c_loc, None, root=0)
        return None
