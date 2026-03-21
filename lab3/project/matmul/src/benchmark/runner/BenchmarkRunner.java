package runner;

import config.BenchmarkConfig;
import io.ResultsExporter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import matrix.MatrixMultiplier;
import parallel.FoxParallelMultiplier;
import parallel.StripedParallelMultiplier;
import results.BenchmarkResult;
import sequential.SequentialMultiplier;
import util.MatrixOps;
import utils.MatrixTestData;

public final class BenchmarkRunner {

    private static final SequentialMultiplier SEQUENTIAL = new SequentialMultiplier();

    private static final String[] BENCH_RESULT_HEADERS =
            new String[] {
                "algorithm",
                "n",
                "threads",
                "q",
                "t_parallel (ms)",
                "t_sequential (ms)",
                "speedup"
            };

    private static final boolean[] BENCH_RESULT_RIGHT =
            new boolean[] {false, true, true, true, true, true, true};

    private BenchmarkRunner() {}

    public static void runVerification() throws Exception {
        int[] sizes = {8, 16, 32};
        int[] stripedThreads = {2, 4, 7};
        int[] foxQ = {2, 2, 4};
        List<String[]> tableRows = new ArrayList<>();

        for (int n : sizes) {
            double[][] a = new double[n][n];
            double[][] b = new double[n][n];
            MatrixTestData.fillDeterministic(a, b);
            double[][] expected = new double[n][n];
            SEQUENTIAL.multiply(a, b, expected);

            for (int t : stripedThreads) {
                double[][] c = new double[n][n];
                MatrixOps.fillZero(c);
                new StripedParallelMultiplier(t).multiply(a, b, c);
                MatrixTestData.assertClose(expected, c, n, "striped n=" + n + " t=" + t);
                tableRows.add(new String[] {String.valueOf(n), "striped", "threads=" + t, "OK"});
            }

            for (int q : foxQ) {
                if (n % q != 0) {
                    continue;
                }
                double[][] c = new double[n][n];
                MatrixOps.fillZero(c);
                new FoxParallelMultiplier(q).multiply(a, b, c);
                MatrixTestData.assertClose(expected, c, n, "fox n=" + n + " q=" + q);
                tableRows.add(new String[] {String.valueOf(n), "fox", "q=" + q, "OK"});
            }
        }

        System.out.println();
        System.out.println("Correctness check (parallel vs sequential reference, not timed)");
        printAsciiTable(
                new String[] {"n", "algorithm", "configuration", "result"},
                tableRows,
                new boolean[] {true, false, false, false});
        System.out.println();
    }

    public static void runBenchmark(BenchmarkConfig cfg) throws Exception {
        Files.createDirectories(cfg.outDir);
        String ts = Instant.now().toString().replace(':', '-');
        String base = cfg.prefix + "_" + ts;
        List<BenchmarkResult> rows = new ArrayList<>();

        String jvm = System.getProperty("java.version") + " " + System.getProperty("java.vendor");
        String os = System.getProperty("os.name") + " " + System.getProperty("os.version");
        String host = java.net.InetAddress.getLocalHost().getHostName();

        List<String[]> meta = new ArrayList<>();
        meta.add(new String[] {"Protocol", "median " + cfg.runs + " runs/phase; warmup 1× sequential per config"});
        meta.add(new String[] {"Output directory", abbreviatePath(cfg.outDir.toAbsolutePath().normalize())});
        meta.add(new String[] {"Matrix sizes n", formatIntArrayForMeta(cfg.sizes)});
        meta.add(new String[] {"Thread counts", formatIntArrayForMeta(cfg.threads)});
        meta.add(
                new String[] {
                    "Algorithms",
                    cfg.striped && cfg.fox
                            ? "striped + fox"
                            : cfg.striped ? "striped" : cfg.fox ? "fox" : "(none)"
                });
        meta.add(new String[] {"Host", host});
        meta.add(new String[] {"OS", os});
        meta.add(new String[] {"JVM", jvm});

        System.out.println();
        System.out.println("Matrix multiply benchmark");
        printAsciiTable(new String[] {"Setting", "Value"}, meta, new boolean[] {false, false});

        List<String> skipNotes = new ArrayList<>();

        int[] benchWidths = benchResultFixedWidths();
        boolean streamingStarted = false;

        for (int n : cfg.sizes) {
            double[][] a = new double[n][n];
            double[][] b = new double[n][n];
            MatrixTestData.fillDeterministic(a, b);

            if (cfg.striped) {
                for (int threads : cfg.threads) {
                    BenchmarkResult row = benchStriped(a, b, n, threads, cfg.runs, jvm, os, host);
                    rows.add(row);
                    streamingStarted =
                            printIntermediateBenchRow(benchWidths, streamingStarted, row);
                }
            }
            if (cfg.fox) {
                for (int threads : cfg.threads) {
                    int q = (int) Math.round(Math.sqrt(threads));
                    if (q * q != threads) {
                        skipNotes.add(
                                "n="
                                        + n
                                        + "  fox  threads="
                                        + threads
                                        + ": skip (need q² threads, e.g. 4, 9, 16)");
                        continue;
                    }
                    if (n % q != 0) {
                        skipNotes.add(
                                "n="
                                        + n
                                        + "  fox  threads="
                                        + threads
                                        + " (q="
                                        + q
                                        + "): skip (n not divisible by q)");
                        continue;
                    }
                    BenchmarkResult row = benchFox(a, b, n, q, threads, cfg.runs, jvm, os, host);
                    rows.add(row);
                    streamingStarted =
                            printIntermediateBenchRow(benchWidths, streamingStarted, row);
                }
            }
        }

        if (streamingStarted) {
            System.out.println(horizontalRule(benchWidths));
            System.out.println();
        }

        List<String[]> resultLines = new ArrayList<>();
        for (BenchmarkResult r : rows) {
            resultLines.add(toResultLine(r));
        }

        if (resultLines.isEmpty()) {
            System.out.println();
            System.out.println("No benchmark rows (check algorithm flags and thread / n constraints).");
        } else {
            System.out.println("Summary (all runs)");
            printAsciiTable(BENCH_RESULT_HEADERS, resultLines, BENCH_RESULT_RIGHT);
        }

        if (!skipNotes.isEmpty()) {
            System.out.println();
            System.out.println("Skipped configurations");
            for (String note : skipNotes) {
                System.out.println("  • " + note);
            }
        }

        Path csvPath = cfg.outDir.resolve(base + ".csv");
        ResultsExporter.writeCsv(csvPath, rows);
        Files.copy(csvPath, cfg.outDir.resolve("latest.csv"), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        System.out.println();
        System.out.println(
                "CSV: "
                        + csvPath.toAbsolutePath().normalize()
                        + "  →  "
                        + cfg.outDir.resolve("latest.csv").toAbsolutePath().normalize());
    }

    /** Short summary so the settings table stays narrow (full list is still in CSV / CLI). */
    private static String formatIntArrayForMeta(int[] values) {
        if (values.length == 0) {
            return "[]";
        }
        String full = Arrays.toString(values);
        if (full.length() <= 72) {
            return full;
        }
        if (values.length == 1) {
            return full;
        }
        int d = values[1] - values[0];
        boolean arithmetic = true;
        for (int i = 1; i < values.length; i++) {
            if (values[i] - values[i - 1] != d) {
                arithmetic = false;
                break;
            }
        }
        if (arithmetic) {
            return values.length
                    + " values: "
                    + values[0]
                    + " … "
                    + values[values.length - 1]
                    + " (step "
                    + d
                    + ")";
        }
        return values.length + " values: " + values[0] + " … " + values[values.length - 1];
    }

    private static String abbreviatePath(Path path) {
        String s = path.toString();
        final int max = 56;
        if (s.length() <= max) {
            return s;
        }
        int keep = (max - 3) / 2;
        return s.substring(0, keep) + " … " + s.substring(s.length() - keep);
    }

    private static String[] toResultLine(BenchmarkResult r) {
        String qStr = r.q == null ? "-" : String.valueOf(r.q);
        return new String[] {
            r.algorithm,
            String.valueOf(r.n),
            String.valueOf(r.threads),
            qStr,
            String.format(Locale.US, "%.2f", r.tParallelMs),
            String.format(Locale.US, "%.2f", r.tSequentialMs),
            String.format(Locale.US, "%.2f", r.speedup),
        };
    }

    /** Column widths for streaming rows (fixed so layout stays stable before later rows exist). */
    private static int[] benchResultFixedWidths() {
        int[] w = new int[BENCH_RESULT_HEADERS.length];
        for (int j = 0; j < w.length; j++) {
            w[j] = BENCH_RESULT_HEADERS[j].length();
        }
        w[0] = Math.max(w[0], 10);
        w[1] = Math.max(w[1], 6);
        w[2] = Math.max(w[2], 8);
        w[3] = Math.max(w[3], 4);
        w[4] = Math.max(w[4], 14);
        w[5] = Math.max(w[5], 14);
        w[6] = Math.max(w[6], 8);
        return w;
    }

    /**
     * Prints one intermediate result row; on first call prints section title and table header.
     *
     * @return true once streaming has started (header printed)
     */
    private static boolean printIntermediateBenchRow(int[] widths, boolean streamingStarted, BenchmarkResult row) {
        if (!streamingStarted) {
            System.out.println();
            System.out.println("Runs (intermediate, one row per configuration as it finishes)");
            System.out.println(horizontalRule(widths));
            printTableRow(widths, BENCH_RESULT_HEADERS, BENCH_RESULT_RIGHT);
            System.out.println(horizontalRule(widths));
        }
        printTableRow(widths, toResultLine(row), BENCH_RESULT_RIGHT);
        return true;
    }

    private static String horizontalRule(int[] widths) {
        StringBuilder rule = new StringBuilder("+");
        for (int width : widths) {
            rule.append("-".repeat(width + 2)).append('+');
        }
        return rule.toString();
    }

    /**
     * Plain ASCII table: column widths from header + cell content. {@code rightAlign[j]} selects
     * right-aligned padding (for numbers).
     */
    private static void printAsciiTable(String[] headers, List<String[]> rows, boolean[] rightAlign) {
        int cols = headers.length;
        int[] w = new int[cols];
        for (int j = 0; j < cols; j++) {
            w[j] = headers[j].length();
        }
        for (String[] row : rows) {
            for (int j = 0; j < cols; j++) {
                w[j] = Math.max(w[j], row[j].length());
            }
        }

        String line = horizontalRule(w);

        System.out.println(line);
        printTableRow(w, headers, rightAlign);
        System.out.println(line);
        for (String[] row : rows) {
            printTableRow(w, row, rightAlign);
        }
        System.out.println(line);
    }

    private static void printTableRow(int[] widths, String[] cells, boolean[] rightAlign) {
        StringBuilder sb = new StringBuilder("|");
        for (int j = 0; j < cells.length; j++) {
            boolean right = rightAlign != null && j < rightAlign.length && rightAlign[j];
            String padded =
                    right
                            ? String.format(Locale.US, "%" + widths[j] + "s", cells[j])
                            : String.format(Locale.US, "%-" + widths[j] + "s", cells[j]);
            sb.append(' ').append(padded).append(" |");
        }
        System.out.println(sb);
    }

    private static BenchmarkResult benchStriped(
            double[][] a, double[][] b, int n, int threads, int runs, String jvm, String os, String host)
            throws Exception {
        double[][] cWarm = new double[n][n];
        SEQUENTIAL.multiply(a, b, cWarm);

        MatrixMultiplier parallel = new StripedParallelMultiplier(threads);

        double[][] cPar = new double[n][n];
        double[][] cSeq = new double[n][n];

        long[] parallelNanos = new long[runs];
        long[] sequentialNanos = new long[runs];

        for (int r = 0; r < runs; r++) {
            MatrixOps.fillZero(cPar);
            long t0 = System.nanoTime();
            parallel.multiply(a, b, cPar);
            parallelNanos[r] = System.nanoTime() - t0;
        }
        for (int r = 0; r < runs; r++) {
            long t0 = System.nanoTime();
            SEQUENTIAL.multiply(a, b, cSeq);
            sequentialNanos[r] = System.nanoTime() - t0;
        }

        double medianPar = medianNanos(parallelNanos);
        double medianSeq = medianNanos(sequentialNanos);
        double speedup = medianSeq / medianPar;

        return new BenchmarkResult(
                "striped",
                n,
                threads,
                null,
                medianPar / 1_000_000.0,
                medianSeq / 1_000_000.0,
                speedup,
                jvm,
                os,
                host);
    }

    private static BenchmarkResult benchFox(
            double[][] a,
            double[][] b,
            int n,
            int q,
            int threads,
            int runs,
            String jvm,
            String os,
            String host)
            throws Exception {
        double[][] cWarm = new double[n][n];
        SEQUENTIAL.multiply(a, b, cWarm);

        MatrixMultiplier parallel = new FoxParallelMultiplier(q);

        double[][] cPar = new double[n][n];
        double[][] cSeq = new double[n][n];

        long[] parallelNanos = new long[runs];
        long[] sequentialNanos = new long[runs];

        for (int r = 0; r < runs; r++) {
            MatrixOps.fillZero(cPar);
            long t0 = System.nanoTime();
            parallel.multiply(a, b, cPar);
            parallelNanos[r] = System.nanoTime() - t0;
        }
        for (int r = 0; r < runs; r++) {
            long t0 = System.nanoTime();
            SEQUENTIAL.multiply(a, b, cSeq);
            sequentialNanos[r] = System.nanoTime() - t0;
        }

        double medianPar = medianNanos(parallelNanos);
        double medianSeq = medianNanos(sequentialNanos);
        double speedup = medianSeq / medianPar;

        return new BenchmarkResult(
                "fox",
                n,
                threads,
                q,
                medianPar / 1_000_000.0,
                medianSeq / 1_000_000.0,
                speedup,
                jvm,
                os,
                host);
    }

    private static double medianNanos(long[] sortedCopy) {
        long[] arr = sortedCopy.clone();
        Arrays.sort(arr);
        int n = arr.length;
        if (n % 2 == 1) {
            return arr[n / 2];
        }
        return (arr[n / 2 - 1] + arr[n / 2]) / 2.0;
    }
}
