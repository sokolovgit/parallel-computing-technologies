package lab4.task1;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ForkJoinPool;
import java.util.stream.Stream;
import lab4.common.Words;

/**
 * Завдання 1: статистика довжини слова (ForkJoin) + бенчмарк. Параметри замірів зафіксовані в константах
 * для звіту; режим запуску — лише опційний аргумент.
 */
public final class Task1Main {

    /** Розігрів і кількість вимірів (як у методичці для лаб. 3). */
    private static final int WARMUP = 2;
    private static final int RUNS = 20;

    /** Скільки разів повторити кожен рядок малого корпусу (щоб замір був «важким»). */
    private static final int REPEAT_SAMPLES = 8000;

    /**
     * Пороги рядків у листі ForkJoin (більше значень → густіша сітка на графіках; час прогону зростає
     * пропорційно кількості комбінацій P×T).
     */
    private static final int[] SWEEP_THRESHOLD_SAMPLES = {
        40, 80, 120, 200, 300, 400, 600, 800, 1200, 1600
    };
    private static final int[] SWEEP_THRESHOLD_CORPUS = {
        80, 120, 200, 300, 400, 500, 600, 800, 1000, 1200, 1600, 2000
    };

    /** Паралелізм ForkJoinPool (є значення більші за кількість ядер — для перевантаження у звіті). */
    private static final int[] SWEEP_PARALLELISM = {1, 2, 3, 4, 5, 6, 8, 10, 12, 16};

    private static final Path DIR_SAMPLES = Paths.get("data/samples");
    private static final Path DIR_CORPUS = Paths.get("data/corpus");

    private static final Path CSV_SAMPLES = Paths.get("results/task1_benchmark.csv");
    private static final Path CSV_CORPUS = Paths.get("results/task1_corpus_benchmark.csv");

    private static int loadedFileCount;

    public static void main(String[] args) throws Exception {
        Path base = Paths.get(System.getProperty("lab4.home", ".")).normalize();
        String mode = args.length == 0 ? "demo" : args[0];

        switch (mode) {
            case "demo" -> runDemo(base);
            case "bench" -> runBenchCsv(base, DIR_SAMPLES, REPEAT_SAMPLES, SWEEP_THRESHOLD_SAMPLES, CSV_SAMPLES);
            case "bench-corpus" -> runBenchCsv(base, DIR_CORPUS, 1, SWEEP_THRESHOLD_CORPUS, CSV_CORPUS);
            default -> {
                System.err.println("Usage: Task1Main [demo | bench | bench-corpus]");
                System.err.println("  demo         — статистика + один бенчмарк у консоль (" + DIR_SAMPLES + ")");
                System.err.println("  bench        — CSV " + CSV_SAMPLES + " (repeat=" + REPEAT_SAMPLES + ")");
                System.err.println("  bench-corpus — CSV " + CSV_CORPUS + " (repeat=1, " + DIR_CORPUS + ")");
                System.exit(1);
            }
        }
    }

    private static void runDemo(Path base) throws IOException {
        String[] raw = loadAllTxtUnder(base, DIR_SAMPLES);
        if (raw.length == 0) {
            System.err.println("No .txt under " + base.resolve(DIR_SAMPLES));
            System.exit(1);
        }
        String[] lines = expandLines(raw, REPEAT_SAMPLES);
        int p = Runtime.getRuntime().availableProcessors();
        int threshold = 400;

        WordLengthStats fork = computeParallel(lines, p, threshold);
        WordLengthStats seq = computeSequential(lines);
        if (!statsRoughlyEqual(fork, seq)) {
            System.err.println("Warning: parallel vs sequential mismatch.");
        }
        printStats("ForkJoin (correctness)", fork);

        System.out.println();
        System.out.println("--- Benchmark (P=" + p + ", threshold=" + threshold + ", runs=" + RUNS + ") ---");
        BenchResult br = benchmark(lines, p, threshold);
        System.out.printf("Mean sequential: %.3f ms%n", br.tSeqMs);
        System.out.printf("Mean ForkJoin:   %.3f ms%n", br.tParMs);
        System.out.printf("Speedup S:       %.3f%n", br.speedup);
        System.out.printf("Efficiency E:    %.3f (P=%d)%n", br.efficiency, p);
    }

    private static void runBenchCsv(Path base, Path dataDir, int repeat, int[] thresholds, Path csvRel)
            throws IOException {
        String[] raw = loadAllTxtUnder(base, dataDir);
        if (raw.length == 0) {
            System.err.println("No .txt under " + base.resolve(dataDir));
            System.exit(1);
        }
        String[] lines = expandLines(raw, repeat);
        Path out = base.resolve(csvRel).normalize();
        Files.createDirectories(out.getParent());

        long wordCount = computeSequential(lines).wordCount();
        String jvm = Runtime.version().toString();
        String os = (System.getProperty("os.name", "") + " " + System.getProperty("os.arch", "")).trim();
        String ts = Instant.now().toString();

        try (BufferedWriter w =
                Files.newBufferedWriter(
                        out, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
            w.write(
                    "task,parallelism,line_threshold,repeat_factor,num_files,num_lines_raw,num_lines_bench,"
                            + "word_count,t_seq_ms,t_par_ms,speedup,efficiency,runs,warmup,jvm,os,timestamp");
            w.newLine();
            for (int t : thresholds) {
                for (int p : SWEEP_PARALLELISM) {
                    if (p < 1) {
                        continue;
                    }
                    BenchResult br = benchmark(lines, p, t);
                    w.write(
                            String.format(
                                    Locale.ROOT,
                                    "task1,%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%d,%d,%s,%s,%s",
                                    p,
                                    t,
                                    repeat,
                                    loadedFileCount,
                                    raw.length,
                                    lines.length,
                                    wordCount,
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

    private static BenchResult benchmark(String[] benchLines, int parallelism, int lineThreshold) {
        for (int w = 0; w < WARMUP; w++) {
            computeSequential(benchLines);
            computeParallel(benchLines, parallelism, lineThreshold);
        }
        long seqTotal = 0;
        for (int r = 0; r < RUNS; r++) {
            long t0 = System.nanoTime();
            computeSequential(benchLines);
            long t1 = System.nanoTime();
            seqTotal += t1 - t0;
        }
        long parTotal = 0;
        try (ForkJoinPool pool = new ForkJoinPool(parallelism)) {
            for (int r = 0; r < RUNS; r++) {
                long t0 = System.nanoTime();
                WordLengthStatsTask task =
                        new WordLengthStatsTask(benchLines, 0, benchLines.length, lineThreshold);
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

    static WordLengthStats computeSequential(String[] lines) {
        WordLengthStats acc = new WordLengthStats();
        for (String line : lines) {
            Words.forEachWordLength(line, acc::addWord);
        }
        return acc;
    }

    static WordLengthStats computeParallel(String[] lines, int parallelism, int lineThreshold) {
        try (ForkJoinPool pool = new ForkJoinPool(parallelism)) {
            WordLengthStatsTask task = new WordLengthStatsTask(lines, 0, lines.length, lineThreshold);
            return pool.invoke(task);
        }
    }

    private static String[] expandLines(String[] base, int repeat) {
        int r = Math.max(1, repeat);
        if (base.length == 0 || r <= 1) {
            return base.clone();
        }
        String[] out = new String[base.length * r];
        for (int i = 0; i < out.length; i++) {
            out[i] = base[i % base.length];
        }
        return out;
    }

    private static boolean statsRoughlyEqual(WordLengthStats a, WordLengthStats b) {
        if (a.wordCount() != b.wordCount()) {
            return false;
        }
        if (Double.compare(a.mean(), b.mean()) != 0) {
            return false;
        }
        return Math.abs(a.standardDeviation() - b.standardDeviation()) < 1e-9;
    }

    private static void printStats(String title, WordLengthStats s) {
        System.out.println(title);
        System.out.println("Word count: " + s.wordCount());
        System.out.printf("Mean length: %.6f%n", s.mean());
        System.out.printf("Std dev (population): %.6f%n", s.standardDeviation());
        System.out.println("Histogram (length -> count); last bucket is >=" + WordLengthStats.BUCKETS + ":");
        long[] h = s.histogramCopy();
        for (int len = 1; len < WordLengthStats.BUCKETS; len++) {
            long c = h[len - 1];
            if (c > 0) {
                System.out.println("  " + len + ": " + c);
            }
        }
        long overflow = h[WordLengthStats.BUCKETS - 1];
        if (overflow > 0) {
            System.out.println("  >=" + WordLengthStats.BUCKETS + ": " + overflow);
        }
    }

    private static String[] loadAllTxtUnder(Path base, Path relativeDir) throws IOException {
        List<Path> files = new ArrayList<>();
        Path root = base.resolve(relativeDir).normalize();
        if (Files.isDirectory(root)) {
            try (Stream<Path> walk = Files.walk(root)) {
                walk.filter(p -> Files.isRegularFile(p) && p.toString().toLowerCase(Locale.ROOT).endsWith(".txt"))
                        .forEach(files::add);
            }
        }
        Collections.sort(files);
        loadedFileCount = files.size();
        List<String> lines = new ArrayList<>();
        for (Path p : files) {
            lines.addAll(Files.readAllLines(p, StandardCharsets.UTF_8));
        }
        return lines.toArray(new String[0]);
    }
}
