package ua.kpi.lab8.benchmark;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class HttpBenchmarkRunner {

    private static final String BASE_URL = "http://localhost:8080/api/multiply/server";
    private static final HttpClient client = HttpClient.newHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    private static final int[] MATRIX_SIZES = {256, 512, 1024};
    private static final int[] GRID_SIZES = {2, 4, 8};
    private static final int ITERATIONS = 3;

    public static void main(String[] args) throws Exception {
        System.out.println("\n===================================================");
        System.out.println("Lab8 HTTP Benchmark Suite");
        System.out.println("===================================================\n");

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

    private static BenchmarkResult runBenchmark(int n, int q) throws Exception {
        System.out.printf("Running benchmark: n=%d, q=%d (threads=%d)%n", n, q, q * q);

        List<Long> times = new ArrayList<>();

        for (int i = 0; i < ITERATIONS; i++) {
            Map<String, Integer> requestBody = Map.of("n", n, "q", q);
            String json = mapper.writeValueAsString(requestBody);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();

            long startTime = System.currentTimeMillis();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            long totalTime = System.currentTimeMillis() - startTime;

            Map<String, Object> result = mapper.readValue(response.body(), Map.class);
            long computationTime = ((Number) result.get("computationTimeMs")).longValue();

            times.add(computationTime);
            System.out.printf("  Iteration %d: computation=%dms, total=%dms%n", 
                    i + 1, computationTime, totalTime);
        }

        long avgTime = (long) times.stream().mapToLong(Long::longValue).average().orElse(0);
        long minTime = times.stream().mapToLong(Long::longValue).min().orElse(0);
        long maxTime = times.stream().mapToLong(Long::longValue).max().orElse(0);

        System.out.printf("  Average: %dms, Min: %dms, Max: %dms%n%n", avgTime, minTime, maxTime);

        return new BenchmarkResult(n, q, q * q, avgTime, minTime, maxTime);
    }

    private static void printSummary(List<BenchmarkResult> results) {
        System.out.println("===================================================");
        System.out.println("BENCHMARK SUMMARY");
        System.out.println("===================================================");
        System.out.printf("%-10s %-10s %-10s %-15s %-10s %-10s %-15s%n",
                "Size (n)", "Grid (q)", "Threads", "Avg Time (ms)", "Min (ms)", "Max (ms)", "Throughput");
        System.out.println("-------------------------------------------------------------------------------------------");

        for (BenchmarkResult result : results) {
            long operations = (long) result.matrixSize * result.matrixSize * result.matrixSize;
            double opsPerSecond = operations / (result.avgTime / 1000.0);
            String throughput = formatOps(opsPerSecond);

            System.out.printf("%-10d %-10d %-10d %-15d %-10d %-10d %-15s%n",
                    result.matrixSize, result.gridSize, result.threads,
                    result.avgTime, result.minTime, result.maxTime, throughput);
        }

        System.out.println("===================================================\n");

        printPerformanceAnalysis(results);
    }

    private static void printPerformanceAnalysis(List<BenchmarkResult> results) {
        System.out.println("PERFORMANCE ANALYSIS");
        System.out.println("===================================================");

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
                    System.out.printf("  q=%d, threads=%d: %.2fx speedup vs q=%d, %s%n",
                            result.gridSize, result.threads, speedup, baseline.gridSize,
                            formatOps(opsPerSecond));
                }
            }
        }

        System.out.println("\n===================================================");
    }

    private static String formatOps(double opsPerSecond) {
        if (opsPerSecond >= 1_000_000_000) {
            return String.format("%.2fG ops/s", opsPerSecond / 1_000_000_000);
        } else if (opsPerSecond >= 1_000_000) {
            return String.format("%.2fM ops/s", opsPerSecond / 1_000_000);
        } else if (opsPerSecond >= 1_000) {
            return String.format("%.2fK ops/s", opsPerSecond / 1_000);
        } else {
            return String.format("%.2f ops/s", opsPerSecond);
        }
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
