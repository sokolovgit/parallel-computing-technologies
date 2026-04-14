# Використовую мову Python 3.10 та бібліотеку mpi4py для роботи з MPI.

import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank, size = comm.rank, comm.size
n = 12

if rank == 0:
    A = np.random.randint(1, 100, (n, n))
    B = np.random.randint(1, 100, (n, n))
    chunks_A = np.array_split(A, size)
    chunks_B = np.array_split(B, size)
else:
    chunks_A = chunks_B = None

local_A = comm.scatter(chunks_A, root=0)
local_B = comm.scatter(chunks_B, root=0)

local_C = (local_A.mean(axis=1) * local_B.mean(axis=1)).astype(int)

total_C = comm.gather(local_C, root=0)

if rank == 0:
    C = np.concatenate(total_C)
    print(f"Result array C:\n{C}")
