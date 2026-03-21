package parallel;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import matrix.MatrixMultiplier;
import util.ExecutorUtils;

/**
 * Striped parallel multiply: for each inner index {@code k}, row bands of {@code C} are updated in
 * parallel (row-row accumulation from the course slides).
 */
public final class StripedParallelMultiplier implements MatrixMultiplier {

    private final int threads;

    public StripedParallelMultiplier(int threads) {
        this.threads = threads;
    }

    @Override
    public void multiply(double[][] a, double[][] b, double[][] c) throws InterruptedException {
        int n = a.length;
        
        if (n == 0) {
            return;
        }

        int workers = Math.max(1, Math.min(threads, n));
        ExecutorService executor = Executors.newFixedThreadPool(workers);

        try {
            for (int k = 0; k < n; k++) {
                CountDownLatch latch = new CountDownLatch(workers);
                final int kf = k;
                for (int t = 0; t < workers; t++) {
                    final int start = t * n / workers;
                    final int end = (t + 1) * n / workers;
                    executor.execute(() -> {
                        try {
                            for (int i = start; i < end; i++) {
                                double aik = a[i][kf];
                                for (int j = 0; j < n; j++) {
                                    c[i][j] += aik * b[kf][j];
                                }
                            }
                        } finally {
                            latch.countDown();
                        }
                    });
                }
                latch.await();
            }
        } finally {
            ExecutorUtils.shutdownQuietly(executor);
        }
    }
}
