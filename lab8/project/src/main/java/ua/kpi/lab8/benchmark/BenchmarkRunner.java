package ua.kpi.lab8.benchmark;

import ua.kpi.lab8.algorithm.FoxParallelMultiplier;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class BenchmarkRunner {

    private static final int[] MATRIX_SIZES = {256, 512, 1024};
    private static final int[] GRID_SIZES = {2, 4, 8};
    private static final int ITERATIONS = 3;

    private final Random random = new Random(42);

    public static void main(String[] args) throws InterruptedException {
        BenchmarkRunner runner = new BenchmarkRunner();
        runner.runAllBenchmarks();
    }

    public void runAllBenchmarks() throws InterruptedException {
        System.out.println("\n=================================================");
        System.out.println("Lab8 Benchmark: Fox Parallel Matrix Multiplication");
        System.out.println("=================================================\n");

        List<BenchmarkResult> results = new ArrayList<>();

        for (int n : MATRIX_SIZES) {
            for (int q : GRID_SIZES) {
                if (n % q == 0) {
                    BenchmarkResult result = runBenchmark(n, q);
                    results.add(result);
                }
            }
        }

        printSummary(results);
    }

    private BenchmarkResult runBenchmark(int n, int q) throws InterruptedException {
        System.out.printf("Running benchmark: n=%d, q=%d (threads=%d)%n", n, q, q * q);

        List<Long> times = new ArrayList<>();

        for (int i = 0; i < ITERATIONS; i++) {
            double[][] matrixA = generateRandomMatrix(n);
            double[][] matrixB = generateRandomMatrix(n);
            double[][] result = new double[n][n];

            FoxParallelMultiplier multiplier = new FoxParallelMultiplier(q);

            long startTime = System.currentTimeMillis();
            multiplier.multiply(matrixA, matrixB, result);
            long endTime = System.currentTimeMillis();

            long time = endTime - startTime;
            times.add(time);
            System.out.printf("  Iteration %d: %dms%n", i + 1, time);
        }

        long avgTime = (long) times.stream().mapToLong(Long::longValue).average().orElse(0);
        long minTime = times.stream().mapToLong(Long::longValue).min().orElse(0);
        long maxTime = times.stream().mapToLong(Long::longValue).max().orElse(0);

        System.out.printf("  Average: %dms, Min: %dms, Max: %dms%n%n", avgTime, minTime, maxTime);

        return new BenchmarkResult(n, q, q * q, avgTime, minTime, maxTime);
    }

    private double[][] generateRandomMatrix(int n) {
        double[][] matrix = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                matrix[i][j] = random.nextDouble() * 10;
            }
        }
        return matrix;
    }

    private void printSummary(List<BenchmarkResult> results) {
        System.out.println("=================================================");
        System.out.println("BENCHMARK SUMMARY");
        System.out.println("=================================================");
        System.out.printf("%-10s %-10s %-10s %-15s %-10s %-10s%n", 
                "Size (n)", "Grid (q)", "Threads", "Avg Time (ms)", "Min (ms)", "Max (ms)");
        System.out.println("-------------------------------------------------");

        for (BenchmarkResult result : results) {
            System.out.printf("%-10d %-10d %-10d %-15d %-10d %-10d%n",
                    result.matrixSize, result.gridSize, result.threads,
                    result.avgTime, result.minTime, result.maxTime);
        }

        System.out.println("=================================================\n");

        printPerformanceAnalysis(results);
    }

    private void printPerformanceAnalysis(List<BenchmarkResult> results) {
        System.out.println("PERFORMANCE ANALYSIS");
        System.out.println("=================================================");

        for (int n : MATRIX_SIZES) {
            System.out.printf("\nMatrix size n=%d:%n", n);
            List<BenchmarkResult> sizeResults = results.stream()
                    .filter(r -> r.matrixSize == n)
                    .toList();

            if (!sizeResults.isEmpty()) {
                BenchmarkResult baseline = sizeResults.get(0);
                for (BenchmarkResult result : sizeResults) {
                    double speedup = (double) baseline.avgTime / result.avgTime;
                    long operations = (long) n * n * n;
                    double opsPerSecond = operations / (result.avgTime / 1000.0);
                    System.out.printf("  q=%d, threads=%d: %.2fx speedup, %.2fM ops/s%n",
                            result.gridSize, result.threads, speedup, opsPerSecond / 1_000_000);
                }
            }
        }

        System.out.println("\n=================================================");
    }

    private static class BenchmarkResult {
        final int matrixSize;
        final int gridSize;
        final int threads;
        final long avgTime;
        final long minTime;
        final long maxTime;

        BenchmarkResult(int matrixSize, int gridSize, int threads, long avgTime, long minTime, long maxTime) {
            this.matrixSize = matrixSize;
            this.gridSize = gridSize;
            this.threads = threads;
            this.avgTime = avgTime;
            this.minTime = minTime;
            this.maxTime = maxTime;
        }
    }
}
