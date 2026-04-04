package lab4.task2;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Locale;
import java.util.concurrent.ForkJoinPool;

/**
 * Завдання 2: стрічкове множення квадратних матриць (як у лаб. 3) через ForkJoin; порівняння з послідовним
 * варіантом і експорт CSV для прискорення.
 */
public final class Task2Main {

    private static final int WARMUP = 2;
    private static final int RUNS = 20;

    /** Мінімальна кількість рядків у листі дерева ForkJoin. */
    private static final int LEAF_ROWS = 32;

    private static final int[] SWEEP_N = {256, 384, 512, 640, 800};
    private static final int[] SWEEP_P = {1, 2, 3, 4, 6, 8, 10, 12, 16};

    private static final int DEMO_N = 512;
    private static final Path CSV_OUT = Paths.get("results/task2_benchmark.csv");

    public static void main(String[] args) throws Exception {
        Path base = Paths.get(System.getProperty("lab4.home", ".")).normalize();
        String mode = args.length == 0 ? "demo" : args[0];

        switch (mode) {
            case "demo" -> runDemo();
            case "bench" -> runBenchCsv(base);
            default -> {
                System.err.println("Usage: Task2Main [demo | bench]");
                System.exit(1);
            }
        }
    }

    private static void runDemo() {
        int n = DEMO_N;
        double[][] a = new double[n][n];
        double[][] b = new double[n][n];
        double[][] cSeq = new double[n][n];
        double[][] cPar = new double[n][n];
        fillDeterministic(a, 1L);
        fillDeterministic(b, 2L);

        sequentialMultiply(a, b, cSeq);
        int p = Runtime.getRuntime().availableProcessors();
        parallelMultiply(a, b, cPar, p, LEAF_ROWS);

        double err = maxAbsDiff(cSeq, cPar);
        System.out.println("Task2 demo: n=" + n + ", max |seq - fj| = " + err);
        if (err > 1e-6) {
            System.err.println("Warning: possible numeric mismatch.");
        }

        System.out.println();
        System.out.println("--- Benchmark (n=" + n + ", P=" + p + ", leafRows=" + LEAF_ROWS + ", runs=" + RUNS + ") ---");
        BenchResult br = benchmarkOnce(n, p, LEAF_ROWS);
        System.out.printf("Mean sequential: %.3f ms%n", br.tSeqMs);
        System.out.printf("Mean ForkJoin:   %.3f ms%n", br.tParMs);
        System.out.printf("Speedup S:       %.3f%n", br.speedup);
        System.out.printf("Efficiency E:    %.3f%n", br.efficiency);
    }

    private static void runBenchCsv(Path base) throws IOException {
        Path out = base.resolve(CSV_OUT).normalize();
        Files.createDirectories(out.getParent());

        String jvm = Runtime.version().toString();
        String os = (System.getProperty("os.name", "") + " " + System.getProperty("os.arch", "")).trim();
        String ts = Instant.now().toString();

        try (BufferedWriter w =
                Files.newBufferedWriter(
                        out, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
            w.write(
                    "task,parallelism,leaf_rows,n,t_seq_ms,t_par_ms,speedup,efficiency,runs,warmup,jvm,os,timestamp");
            w.newLine();

            for (int n : SWEEP_N) {
                int leaf = Math.min(LEAF_ROWS, Math.max(8, n / 16));
                for (int p : SWEEP_P) {
                    if (p < 1) {
                        continue;
                    }
                    BenchResult br = benchmarkOnce(n, p, leaf);
                    w.write(
                            String.format(
                                    Locale.ROOT,
                                    "task2,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%d,%d,%s,%s,%s",
                                    p,
                                    leaf,
                                    n,
                                    br.tSeqMs,
                                    br.tParMs,
                                    br.speedup,
                                    br.efficiency,
                                    RUNS,
                                    WARMUP,
                                    csvEscape(jvm),
                                    csvEscape(os),
                                    csvEscape(ts)));
                    w.newLine();
                }
            }
        }
        System.out.println("Wrote " + out.toAbsolutePath());
    }

    private static String csvEscape(String s) {
        if (s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }

    private record BenchResult(double tSeqMs, double tParMs, double speedup, double efficiency) {}

    private static BenchResult benchmarkOnce(int n, int parallelism, int leafRows) {
        double[][] a = new double[n][n];
        double[][] b = new double[n][n];
        double[][] c = new double[n][n];
        fillDeterministic(a, 1L);
        fillDeterministic(b, 2L);

        for (int w = 0; w < WARMUP; w++) {
            sequentialMultiply(a, b, c);
            parallelMultiply(a, b, c, parallelism, leafRows);
        }

        long seqTotal = 0;
        for (int r = 0; r < RUNS; r++) {
            long t0 = System.nanoTime();
            sequentialMultiply(a, b, c);
            long t1 = System.nanoTime();
            seqTotal += t1 - t0;
        }

        long parTotal = 0;
        try (ForkJoinPool pool = new ForkJoinPool(parallelism)) {
            for (int r = 0; r < RUNS; r++) {
                long t0 = System.nanoTime();
                StripedMatMulTask task = new StripedMatMulTask(a, b, c, 0, n, leafRows);
                pool.invoke(task);
                long t1 = System.nanoTime();
                parTotal += t1 - t0;
            }
        }

        double tSeqNs = (double) seqTotal / RUNS;
        double tParNs = (double) parTotal / RUNS;
        double speedup = tParNs > 0 ? tSeqNs / tParNs : 0.0;
        double eff = parallelism > 0 ? speedup / parallelism : 0.0;
        return new BenchResult(tSeqNs / 1_000_000.0, tParNs / 1_000_000.0, speedup, eff);
    }

    static void sequentialMultiply(double[][] a, double[][] b, double[][] c) {
        int n = a.length;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                double sum = 0.0;
                for (int k = 0; k < n; k++) {
                    sum += a[i][k] * b[k][j];
                }
                c[i][j] = sum;
            }
        }
    }

    static void parallelMultiply(double[][] a, double[][] b, double[][] c, int parallelism, int leafRows) {
        try (ForkJoinPool pool = new ForkJoinPool(parallelism)) {
            StripedMatMulTask task = new StripedMatMulTask(a, b, c, 0, a.length, leafRows);
            pool.invoke(task);
        }
    }

    private static void fillDeterministic(double[][] m, long seed) {
        java.util.Random rnd = new java.util.Random(seed);
        for (double[] row : m) {
            for (int j = 0; j < row.length; j++) {
                row[j] = rnd.nextDouble();
            }
        }
    }

    private static double maxAbsDiff(double[][] x, double[][] y) {
        double max = 0.0;
        for (int i = 0; i < x.length; i++) {
            for (int j = 0; j < x[i].length; j++) {
                max = Math.max(max, Math.abs(x[i][j] - y[i][j]));
            }
        }
        return max;
    }
}
