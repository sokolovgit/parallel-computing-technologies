"""Small-N correctness check for all algorithms (run under mpirun)."""

from __future__ import annotations

import numpy as np
from mpi4py import MPI

from matrix_multiplication.registry import ALGOS

N = 16

_ALGO_LABELS: dict[str, str] = {
    "p2p": "MPI_Send / MPI_Recv (point-to-point)",
    "collective_sbg": "MPI_Scatterv + MPI_Bcast + MPI_Gatherv",
    "p2p_gatherv": "P2P distribute A,B + MPI_Gatherv for C",
    "allgatherv": "Scatterv + Bcast + MPI_Allgatherv",
}


def main() -> None:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    _pn = MPI.Get_processor_name()
    proc_name = _pn.decode() if isinstance(_pn, bytes) else str(_pn)

    if rank == 0:
        a = np.full((N, N), 10.0, dtype=np.float64)
        b = np.full((N, N), 10.0, dtype=np.float64)
        expected = a @ b
    else:
        a = b = expected = None

    if rank == 0:
        print("=" * 60)
        print("matrix_multiplication — demo (correctness)")
        print("=" * 60)
        print(f"MPI processes: {size}  |  matrix order N: {N}")
        print(f"Rank 0 host: {proc_name}")
        print(f"dtype: {np.float64.__name__}  |  fill: A_ij = B_ij = 10.0")
        print(f"Reference C = A @ B: shape {expected.shape}, sample C[0,0] = {expected[0, 0]:.1f}")
        print()
        print(f"Algorithms under test ({len(ALGOS)}):")
        for key in ALGOS:
            label = _ALGO_LABELS.get(key, "")
            extra = f" — {label}" if label else ""
            print(f"  • {key}{extra}")
        print("-" * 60)

    for name, algo in ALGOS.items():
        comm.Barrier()
        if rank == 0:
            t0 = MPI.Wtime()
        c = algo.multiply(comm, a, b)
        comm.Barrier()
        if rank == 0:
            t1 = MPI.Wtime()
            assert c is not None
            assert expected is not None
            err = c - expected
            max_abs = float(np.max(np.abs(err)))
            rms = float(np.sqrt(np.mean(err**2)))
            ok = np.allclose(c, expected, rtol=0.0, atol=1e-9)
            elapsed_ms = (t1 - t0) * 1000.0
            status = "PASS" if ok else "FAIL"
            print(f"[{name}]")
            print(f"  wall time (rank 0): {elapsed_ms:.4f} ms")
            print(f"  max |C - ref|:      {max_abs:.3e}")
            print(f"  RMS error:          {rms:.3e}")
            print(f"  result:             {status}")
            if not ok:
                print("demo: aborting on first failure.")
                raise SystemExit(1)
            print()

    if rank == 0:
        print("-" * 60)
        print(f"demo finished: all {len(ALGOS)} algorithms passed.")
        print("=" * 60)


if __name__ == "__main__":
    main()
