/**
 * Lab 6, task 3: parallel matrix multiply C = A * B using non-blocking MPI_Isend / MPI_Irecv + Wait / Waitall.
 * Same data flow as task 2 (master distributes row strips of A and full B; workers return C strips).
 *
 * Usage: mpirun -np P ./task3_mm_nonblocking [NRA NCA NCB] [--bench]
 *   Default dimensions: 62 x 15 and 15 x 7. Need P >= 2.
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
                    "mpi_mm (non-blocking MPI): tasks=%d workers=%d | A[%d x %d] * B[%d x %d] => C[%d x %d]\n",
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
            MPI_Request sreq[4];
            MPI_Isend(&offset, 1, MPI_INT, dest, TAG_FROM_MASTER, MPI_COMM_WORLD, &sreq[0]);
            MPI_Isend(&rows, 1, MPI_INT, dest, TAG_FROM_MASTER, MPI_COMM_WORLD, &sreq[1]);
            MPI_Isend(
                    a + (size_t)offset * (size_t)nca,
                    rows * nca,
                    MPI_DOUBLE,
                    dest,
                    TAG_FROM_MASTER,
                    MPI_COMM_WORLD,
                    &sreq[2]);
            MPI_Isend(b, nca * ncb, MPI_DOUBLE, dest, TAG_FROM_MASTER, MPI_COMM_WORLD, &sreq[3]);
            MPI_Waitall(4, sreq, MPI_STATUS_IGNORE);
            offset += rows;
        }

        int *off_buf = calloc((size_t)(numworkers + 1), sizeof(int));
        int *rows_buf = calloc((size_t)(numworkers + 1), sizeof(int));
        MPI_Request *meta_req = malloc(sizeof(MPI_Request) * (size_t)(2 * numworkers));
        MPI_Request *c_req = malloc(sizeof(MPI_Request) * (size_t)numworkers);
        if (!off_buf || !rows_buf || !meta_req || !c_req) {
            perror("malloc");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        for (int s = 1; s <= numworkers; s++) {
            MPI_Irecv(
                    &off_buf[s],
                    1,
                    MPI_INT,
                    s,
                    TAG_FROM_WORKER,
                    MPI_COMM_WORLD,
                    &meta_req[(size_t)(s - 1) * 2U]);
            MPI_Irecv(
                    &rows_buf[s],
                    1,
                    MPI_INT,
                    s,
                    TAG_FROM_WORKER,
                    MPI_COMM_WORLD,
                    &meta_req[(size_t)(s - 1) * 2U + 1U]);
        }
        MPI_Waitall(2 * numworkers, meta_req, MPI_STATUS_IGNORE);

        for (int s = 1; s <= numworkers; s++) {
            MPI_Irecv(
                    c + (size_t)off_buf[s] * (size_t)ncb,
                    rows_buf[s] * ncb,
                    MPI_DOUBLE,
                    s,
                    TAG_FROM_WORKER,
                    MPI_COMM_WORLD,
                    &c_req[(size_t)(s - 1)]);
        }
        MPI_Waitall(numworkers, c_req, MPI_STATUS_IGNORE);

        double t1 = MPI_Wtime();
        if (bench) {
            printf("nonblocking,%d,%d,%d,%d,%.9f\n", nra, nca, ncb, numtasks, t1 - t0);
        }

        for (int s = 1; s <= numworkers; s++) {
            if (!bench) {
                printf("Received results from task %d\n", s);
            }
        }

        free(meta_req);
        free(c_req);
        free(off_buf);
        free(rows_buf);

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
        int offset = 0;
        int rows = 0;
        MPI_Request rmeta[2];
        MPI_Irecv(&offset, 1, MPI_INT, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &rmeta[0]);
        MPI_Irecv(&rows, 1, MPI_INT, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &rmeta[1]);
        MPI_Waitall(2, rmeta, MPI_STATUS_IGNORE);

        double *a = malloc((size_t)rows * (size_t)nca * sizeof(double));
        double *b = malloc((size_t)nca * (size_t)ncb * sizeof(double));
        double *c = malloc((size_t)rows * (size_t)ncb * sizeof(double));
        if (!a || !b || !c) {
            perror("malloc");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        MPI_Request rdata[2];
        MPI_Irecv(a, rows * nca, MPI_DOUBLE, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &rdata[0]);
        MPI_Irecv(b, nca * ncb, MPI_DOUBLE, MASTER, TAG_FROM_MASTER, MPI_COMM_WORLD, &rdata[1]);
        MPI_Waitall(2, rdata, MPI_STATUS_IGNORE);

        for (int k = 0; k < ncb; k++) {
            for (int i = 0; i < rows; i++) {
                c[(size_t)i * (size_t)ncb + (size_t)k] = 0.0;
                for (int j = 0; j < nca; j++) {
                    c[(size_t)i * (size_t)ncb + (size_t)k] +=
                            a[(size_t)i * (size_t)nca + (size_t)j] * b[(size_t)j * (size_t)ncb + (size_t)k];
                }
            }
        }

        /* Post metadata first and wait: master only Irecv's C after all (offset,rows) pairs arrive. */
        MPI_Request sback[3];
        MPI_Isend(&offset, 1, MPI_INT, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD, &sback[0]);
        MPI_Isend(&rows, 1, MPI_INT, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD, &sback[1]);
        MPI_Waitall(2, sback, MPI_STATUS_IGNORE);
        MPI_Isend(c, rows * ncb, MPI_DOUBLE, MASTER, TAG_FROM_WORKER, MPI_COMM_WORLD, &sback[0]);
        MPI_Wait(&sback[0], MPI_STATUS_IGNORE);

        free(a);
        free(b);
        free(c);
    }

    MPI_Finalize();
    return 0;
}
