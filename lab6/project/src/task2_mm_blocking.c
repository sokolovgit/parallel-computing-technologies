/**
 * Lab 6, task 2: parallel matrix multiply C = A * B using blocking MPI_Send / MPI_Recv.
 * Master (rank 0) distributes row blocks of A and full B to workers; workers return blocks of C.
 * Based on LLNL "mpi_mm.c" (Blaise Barney); fixed typos from the lab handout; dynamic allocation.
 *
 * Usage: mpirun -np P ./task2_mm_blocking [NRA NCA NCB] [--bench]
 *   Default dimensions: 62 x 15 and 15 x 7 (listing 1). Need P >= 2.
 *   --bench: one CSV line to stdout; quiet (task 4 timing).
 */
#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MASTER 0
#define TAG_FROM_MASTER 1
#define TAG_FROM_WORKER 2

static void usage(const char *prog) {
    fprintf(stderr, "Usage: %s [NRA NCA NCB] [--bench]\n", prog);
    fprintf(stderr, "  Default: 62 15 7 (matrix A is NRA x NCA, B is NCA x NCB)\n");
    fprintf(stderr, "  --bench: quiet; print one CSV line to stdout (variant, dims, procs, wall seconds)\n");
}

int main(int argc, char **argv) {
    int nra = 62;
    int nca = 15;
    int ncb = 7;
    int bench = 0;
    int eff_argc = argc;
    if (eff_argc >= 2 && strcmp(argv[eff_argc - 1], "--bench") == 0) {
        bench = 1;
        eff_argc--;
    }

    if (eff_argc == 1) {
        /* defaults */
    } else if (eff_argc == 4) {
        nra = atoi(argv[1]);
        nca = atoi(argv[2]);
        ncb = atoi(argv[3]);
        if (nra < 1 || nca < 1 || ncb < 1) {
            usage(argv[0]);
            return 1;
        }
    } else {
        usage(argv[0]);
        return 1;
    }

    MPI_Init(&argc, &argv);

    int numtasks;
    int taskid;
    MPI_Comm_size(MPI_COMM_WORLD, &numtasks);
    MPI_Comm_rank(MPI_COMM_WORLD, &taskid);

    if (numtasks < 2) {
        if (taskid == MASTER) {
            fprintf(stderr, "Need at least two MPI processes.\n");
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int numworkers = numtasks - 1;

    if (taskid == MASTER) {
        size_t sa = (size_t)nra * (size_t)nca;
        size_t sb = (size_t)nca * (size_t)ncb;
        size_t sc = (size_t)nra * (size_t)ncb;
        double *a = malloc(sa * sizeof(double));
        double *b = malloc(sb * sizeof(double));
        double *c = calloc(sc, sizeof(double));
        if (!a || !b || !c) {
            perror("malloc");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        for (int i = 0; i < nra; i++) {
            for (int j = 0; j < nca; j++) {
                a[(size_t)i * (size_t)nca + (size_t)j] = 10.0;
            }
        }
        for (int i = 0; i < nca; i++) {
            for (int j = 0; j < ncb; j++) {
                b[(size_t)i * (size_t)ncb + (size_t)j] = 10.0;
            }
        }

        int averow = nra / numworkers;
        int extra = nra % numworkers;
        int offset = 0;

        if (!bench) {
            printf(
                    "mpi_mm (blocking MPI): tasks=%d workers=%d | A[%d x %d] * B[%d x %d] => C[%d x %d]\n",
                    numtasks,
                    numworkers,
                    nra,
                    nca,
                    nca,
                    ncb,
                    nra,
                    ncb);
        }

        double t0 = MPI_Wtime();
        for (int dest = 1; dest <= numworkers; dest++) {
            int rows = (dest <= extra) ? averow + 1 : averow;
            if (!bench) {
                printf("Sending %d rows to task %d offset=%d\n", rows, dest, offset);
            }
            MPI_Send(&offset, 1, MPI_INT, dest, TAG_FROM_MASTER, MPI_COMM_WORLD);
            MPI_Send(&rows, 1, MPI_INT, dest, TAG_FROM_MASTER, MPI_COMM_WORLD);
            MPI_Send(
                    a + (size_t)offset * (size_t)nca,
                    rows * nca,
                    MPI_DOUBLE,
                    dest,
                    TAG_FROM_MASTER,
                    MPI_COMM_WORLD);
            MPI_Send(b, nca * ncb, MPI_DOUBLE, dest, TAG_FROM_MASTER, MPI_COMM_WORLD);
            offset += rows;
        }

        MPI_Status status;
        for (int source = 1; source <= numworkers; source++) {
            int off;
            int rows;
            MPI_Recv(&off, 1, MPI_INT, source, TAG_FROM_WORKER, MPI_COMM_WORLD, &status);
            MPI_Recv(&rows, 1, MPI_INT, source, TAG_FROM_WORKER, MPI_COMM_WORLD, &status);
            MPI_Recv(
                    c + (size_t)off * (size_t)ncb,
                    rows * ncb,
                    MPI_DOUBLE,
                    source,
                    TAG_FROM_WORKER,
                    MPI_COMM_WORLD,
                    &status);
            if (!bench) {
                printf("Received results from task %d\n", source);
            }
        }
        double t1 = MPI_Wtime();
        if (bench) {
            printf("blocking,%d,%d,%d,%d,%.9f\n", nra, nca, ncb, numtasks, t1 - t0);
        }

        double expected = (double)nca * 100.0;
        int ok = 1;
        for (int i = 0; i < nra && ok; i++) {
            for (int j = 0; j < ncb; j++) {
                double v = c[(size_t)i * (size_t)ncb + (size_t)j];
                if (fabs(v - expected) > 1e-6) {
                    printf("Mismatch C[%d,%d]=%.6f expected %.6f\n", i, j, v, expected);
                    ok = 0;
                    break;
                }
            }
        }
        if (!bench) {
            printf("Verification: %s (each C[i,j] should be %.6f for fill 10)\n", ok ? "OK" : "FAIL", expected);
        } else if (!ok) {
            fprintf(stderr, "Verification FAIL (bench mode)\n");
        }

        if (!bench && nra * ncb <= 400) {
            printf("****\nResult matrix C:\n");
            for (int i = 0; i < nra; i++) {
                for (int j = 0; j < ncb; j++) {
                    printf("%8.2f ", c[(size_t)i * (size_t)ncb + (size_t)j]);
                }
                printf("\n");
            }
            printf("********\n");
        } else if (!bench) {
            printf(
                    "C too large to print; sample C[0,0]=%.2f C[%d,%d]=%.2f\n",
                    c[0],
                    nra - 1,
                    ncb - 1,
                    c[(size_t)(nra - 1) * (size_t)ncb + (size_t)(ncb - 1)]);
        }
        if (!bench) {
            printf("Done.\n");
        }

        free(a);
        free(b);
        free(c);
    } else {
        (void)bench;
        int offset;
        int rows;
        MPI_Status status;

        MPI_Recv(&offset, 1, MPI_INT, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &status);
        MPI_Recv(&rows, 1, MPI_INT, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &status);

        double *a = malloc((size_t)rows * (size_t)nca * sizeof(double));
        double *b = malloc((size_t)nca * (size_t)ncb * sizeof(double));
        double *c = malloc((size_t)rows * (size_t)ncb * sizeof(double));
        if (!a || !b || !c) {
            perror("malloc");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        MPI_Recv(a, rows * nca, MPI_DOUBLE, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &status);
        MPI_Recv(b, nca * ncb, MPI_DOUBLE, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &status);

        for (int k = 0; k < ncb; k++) {
            for (int i = 0; i < rows; i++) {
                c[(size_t)i * (size_t)ncb + (size_t)k] = 0.0;
                for (int j = 0; j < nca; j++) {
                    c[(size_t)i * (size_t)ncb + (size_t)k] +=
                            a[(size_t)i * (size_t)nca + (size_t)j] * b[(size_t)j * (size_t)ncb + (size_t)k];
                }
            }
        }

        MPI_Send(&offset, 1, MPI_INT, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD);
        MPI_Send(&rows, 1, MPI_INT, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD);
        MPI_Send(c, rows * ncb, MPI_DOUBLE, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD);

        free(a);
        free(b);
        free(c);
    }

    MPI_Finalize();
    return 0;
}
