# Використовую мову Python 3.10 та бібліотеку mpi4py для роботи з MPI.

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank, size = comm.rank, comm.size

chunks = None
if rank == 0:
    A = ["Toyota", "Honda", "Ford", "BMW", "Audi", "Chevrolet", "Kia", "Mazda"]
    chunks = [None] + [A[i :: size - 1] for i in range(size - 1)]

chunk = comm.scatter(chunks, root=0)

first_val = None
if rank > 0 and chunk:
    chunk.sort()
    first_val = chunk[0]
    print(f"Worker {rank} sorted chunk: {chunk}")

results = comm.gather(first_val, root=0)

if rank == 0:
    print(f"Master received: {list(filter(None, results))}")
