# Використовую мову Python 3.10 та бібліотеку mpi4py для роботи з MPI.

from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

arr = np.array([rank + 1, rank + 2, rank + 3], dtype=np.float64)

sum = np.zeros_like(arr)
comm.Allreduce(arr, sum, op=MPI.SUM)

print(f"Rank {rank}: arr={arr}, sum={sum}")
