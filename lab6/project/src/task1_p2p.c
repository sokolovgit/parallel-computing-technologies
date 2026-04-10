/**
 * Lab 6, task 1: minimal point-to-point demo — blocking (MPI_Send/MPI_Recv)
 * and non-blocking (MPI_Isend/MPI_Irecv + MPI_Wait).
 * Run: mpirun -np 2 ./bin/task1_p2p   (or: just task1)
 */
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

enum { TAG_BLOCK = 100, TAG_NONBLOCK = 200 };

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int rank;
    int size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size < 2) {
        if (rank == 0) {
            fprintf(stderr, "Need at least 2 MPI processes (e.g. mpirun -np 2 ...).\n");
        }
        MPI_Finalize();
        return 1;
    }

    if (rank == 0) {
        printf("=== Lab 6, task 1: point-to-point demo (%d processes) ===\n", size);
        fflush(stdout);
    }

    /* --- Blocking exchange: rank 0 -> rank 1 --- */
    if (rank == 0) {
        int msg = 42;
        MPI_Send(&msg, 1, MPI_INT, 1, TAG_BLOCK, MPI_COMM_WORLD);
        printf("[blocking] rank 0 sent value %d to rank 1 (tag %d)\n", msg, TAG_BLOCK);
        fflush(stdout);
    } else if (rank == 1) {
        int buf = 0;
        MPI_Status st;
        MPI_Recv(&buf, 1, MPI_INT, 0, TAG_BLOCK, MPI_COMM_WORLD, &st);
        printf("[blocking] rank 1 received %d (source=%d, tag=%d)\n",
               buf,
               st.MPI_SOURCE,
               st.MPI_TAG);
        fflush(stdout);
    }

    MPI_Barrier(MPI_COMM_WORLD);

    /* --- Non-blocking: rank 0 -> rank 1 --- */
    if (rank == 0) {
        int msg = 7;
        MPI_Request req;
        MPI_Isend(&msg, 1, MPI_INT, 1, TAG_NONBLOCK, MPI_COMM_WORLD, &req);
        /* Buffer msg must not be touched until Wait completes. */
        MPI_Wait(&req, MPI_STATUS_IGNORE);
        printf("[nonblocking] rank 0 Isend finished (sent %d)\n", msg);
        fflush(stdout);
    } else if (rank == 1) {
        int buf = 0;
        MPI_Request req;
        MPI_Irecv(&buf, 1, MPI_INT, 0, TAG_NONBLOCK, MPI_COMM_WORLD, &req);
        MPI_Wait(&req, MPI_STATUS_IGNORE);
        printf("[nonblocking] rank 1 Irecv finished (received %d)\n", buf);
        fflush(stdout);
    }

    MPI_Barrier(MPI_COMM_WORLD);

    if (rank == 0) {
        printf("=== Done ===\n");
        fflush(stdout);
    }

    MPI_Finalize();
    return 0;
}
