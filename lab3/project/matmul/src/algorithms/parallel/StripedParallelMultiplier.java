package parallel;

import matrix.MatrixMultiplier;

/**
 * Row-band striped multiply (same approach as {@code StripeMatrixMultiplication} in the course
 * reference): each thread owns a contiguous row range and computes full dot products for those rows.
 */
public final class StripedParallelMultiplier implements MatrixMultiplier {

    private final int numProcessors;

    public StripedParallelMultiplier(int numProcessors) {
        this.numProcessors = numProcessors;
    }

    @Override
    public void multiply(double[][] a, double[][] b, double[][] c) throws InterruptedException {
        int n = a.length;
        if (n == 0) {
            return;
        }

        int workers = Math.max(1, Math.min(numProcessors, n));
        Thread[] threads = new Thread[workers];
        int rowsPerThread = n / workers;
        int remainder = n % workers;
        int startRow = 0;
        for (int i = 0; i < workers; i++) {
            int rows = rowsPerThread + (i < remainder ? 1 : 0);
            int endRow = startRow + rows;
            final int sRow = startRow;
            final int eRow = endRow;
            threads[i] =
                    new Thread(
                            () -> {
                                for (int row = sRow; row < eRow; row++) {
                                    for (int j = 0; j < n; j++) {
                                        double sum = 0.0;
                                        for (int k = 0; k < n; k++) {
                                            sum += a[row][k] * b[k][j];
                                        }
                                        c[row][j] = sum;
                                    }
                                }
                            });
            startRow = endRow;
        }
        for (Thread thread : threads) {
            thread.start();
        }
        for (Thread thread : threads) {
            thread.join();
        }
    }
}
