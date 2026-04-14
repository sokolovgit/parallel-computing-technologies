package mkr2.java;

import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveTask;
import java.util.Random;

public class task18 {

    private static final int N = 100_000;
    private static final int PARALLELISM = 12;

    public static void main(String[] args) {
        double[] data = new double[N];
        Random rng = new Random(888);

        for (int i = 0; i < N; i++) {
            data[i] = rng.nextDouble() * 100;
        }

        try (ForkJoinPool pool = new ForkJoinPool(PARALLELISM)) {
            double result = pool.invoke(new CascadeSumTask(data, 0, N));
            System.out.println("Sum = " + result);
        }
    }

    static class CascadeSumTask extends RecursiveTask<Double> {
        private final double[] arr;
        private final int from;
        private final int to;
        private static final int THRESHOLD = 1000;

        CascadeSumTask(double[] arr, int from, int to) {
            this.arr = arr;
            this.from = from;
            this.to = to;
        }

        @Override
        protected Double compute() {
            int n = to - from;

            if (n <= THRESHOLD) {
                double sum = 0;
                for (int i = from; i < to; i++) {
                    sum += arr[i];
                }

                return sum;
            }

            int mid = from + n / 2;
            CascadeSumTask left = new CascadeSumTask(arr, from, mid);
            CascadeSumTask right = new CascadeSumTask(arr, mid, to);

            left.fork();
            double rSum = right.compute();
            double lSum = left.join();

            return lSum + rSum;
        }
    }
}
