package parallel;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import matrix.MatrixMultiplier;
import util.ExecutorUtils;

/**
 * Fox block algorithm on a {@code q&times;q} grid; {@code q}<sup>2</sup> tasks per phase. Requires
 * {@code n % q == 0}.
 */
public final class FoxParallelMultiplier implements MatrixMultiplier {

    private final int q;

    public FoxParallelMultiplier(int q) {
        this.q = q;
    }

    @Override
    public void multiply(double[][] a, double[][] b, double[][] c) throws InterruptedException {
        int n = a.length;

        if (n == 0) {
            return;
        }

        if (q < 1 || n % q != 0) {
            throw new IllegalArgumentException("n must be divisible by q");
        }

        int m = n / q;
        int workers = q * q;
        
        ExecutorService executor = Executors.newFixedThreadPool(workers);
        try {
            for (int k = 0; k < q; k++) {
                CountDownLatch latch = new CountDownLatch(workers);
                final int kf = k;
                for (int bi = 0; bi < q; bi++) {
                    for (int bj = 0; bj < q; bj++) {
                        final int biF = bi;
                        final int bjF = bj;
                        executor.execute(() -> {
                            try {
                                int aRow0 = biF * m;
                                int aCol0 = ((biF + kf) % q) * m;
                                int bRow0 = ((biF + kf) % q) * m;
                                int bCol0 = bjF * m;
                                int cRow0 = biF * m;
                                int cCol0 = bjF * m;
                                blockMultiplyAdd(a, aRow0, aCol0, b, bRow0, bCol0, c, cRow0, cCol0, m);
                            } finally {
                                latch.countDown();
                            }
                        });
                    }
                }
                latch.await();
            }
        } finally {
            ExecutorUtils.shutdownQuietly(executor);
        }
    }

    private static void blockMultiplyAdd(
            double[][] a,
            int aRow0,
            int aCol0,
            double[][] b,
            int bRow0,
            int bCol0,
            double[][] c,
            int cRow0,
            int cCol0,
            int m) {
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < m; j++) {
                double sum = 0.0;
                for (int kk = 0; kk < m; kk++) {
                    sum += a[aRow0 + i][aCol0 + kk] * b[bRow0 + kk][bCol0 + j];
                }
                c[cRow0 + i][cCol0 + j] += sum;
            }
        }
    }
}
