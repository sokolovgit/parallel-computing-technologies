# Використовую мову Python 3.10 та бібліотеку mpi4py для роботи з MPI.

from mpi4py import MPI
import numpy as np

TAG = 888

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

n_days = 100
temperature_data = np.zeros(n_days)

if rank == 2:
    temperature_data = np.random.uniform(-10.0, 35.0, n_days)
    req = comm.Isend(temperature_data, dest=0, tag=TAG)
    req.Wait()

    print(f"Process {rank} sent data")

if rank == 0:
    req = comm.Irecv(temperature_data, source=2, tag=TAG)
    req.Wait()

    print(f"Process {rank} received data")
