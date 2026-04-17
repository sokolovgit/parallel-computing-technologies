"""
Single MPI job: read LAB7_MODE from env, print one CSV line on rank 0.

Invoked by run_benchmarks via mpirun.
"""

from __future__ import annotations

import os

import numpy as np
from mpi4py import MPI

from matrix_multiplication.registry import ALGOS


def main() -> None:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    mode = os.environ.get("LAB7_MODE", "collective_sbg")
    n = int(os.environ.get("LAB7_N", "100"))

    if mode not in ALGOS:
        if rank == 0:
            print(f"unknown LAB7_MODE={mode}", flush=True)
        raise SystemExit(2)

    algo = ALGOS[mode]

    if rank == 0:
        a = np.full((n, n), 10.0, dtype=np.float64)
        b = np.full((n, n), 10.0, dtype=np.float64)
    else:
        a = b = None

    comm.Barrier()
    t0 = MPI.Wtime()
    _ = algo.multiply(comm, a, b)
    comm.Barrier()
    t1 = MPI.Wtime()

    if rank == 0:
        elapsed = t1 - t0
        print(f"{mode},{n},{n},{n},{size},{elapsed:.9f}", flush=True)


if __name__ == "__main__":
    main()
