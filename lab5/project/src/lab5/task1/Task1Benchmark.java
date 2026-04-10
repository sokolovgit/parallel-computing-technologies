package lab5.task1;

import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import lab5.common.SimulationConfig;
import lab5.common.SimulationResult;
import lab5.smo.MultiChannelSmo;

/**
 * Batch runs for plotting: sweeps mean inter-arrival time and queue capacity; writes
 * {@code results/lab5_by_load.csv} and {@code results/lab5_by_queue.csv}. Invoked by {@code just task1-plots}.
 */
public final class Task1Benchmark {

    private static final String CSV_HEADER =
            "sweep,meanIA_ms,channels,queue,rep,seed,meanQueue,P_reject,arrivals,rejected,served,qSamples,wall_s";

    private static final int MIN_SERVED = 1000;
    private static final long SAMPLE_INTERVAL_MS = 2L;
    private static final int CHANNELS = 4;
    private static final int DEFAULT_QUEUE = 8;
    private static final double SERV_MEAN_MS = 0.25;
    private static final double SERV_STD_MS = 0.06;
    private static final int REPS_PER_POINT = 20;

    private Task1Benchmark() {}

    public static void main(String[] args) throws Exception {
        String home = System.getProperty("lab5.home", ".");
        Path base = Paths.get(home).normalize();
        Path results = base.resolve("results");
        Files.createDirectories(results);

        Path byLoad = results.resolve("lab5_by_load.csv");
        Path byQueue = results.resolve("lab5_by_queue.csv");

        System.err.println("Writing " + byLoad + " (this may take a minute)...");
        runLoadSweep(byLoad);
        System.err.println("Writing " + byQueue + "...");
        runQueueSweep(byQueue);
        System.err.println("Done.");
    }

    /** Vary mean inter-arrival time (ms); lower = heavier load. */
    private static void runLoadSweep(Path out) throws Exception {
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out, StandardCharsets.UTF_8))) {
            w.println(CSV_HEADER);
            for (double meanIa = 0.02; meanIa <= 0.1000001; meanIa += 0.01) {
                double ia = Math.round(meanIa * 100.0) / 100.0;
                for (int rep = 0; rep < REPS_PER_POINT; rep++) {
                    long seed = mixSeed(CHANNELS, DEFAULT_QUEUE, ia, rep, 1);
                    writeOneRun(w, "by_load", ia, CHANNELS, DEFAULT_QUEUE, rep, seed);
                }
            }
        }
    }

    /** Vary queue capacity at fixed moderate load. */
    private static void runQueueSweep(Path out) throws Exception {
        double meanIa = 0.05;
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out, StandardCharsets.UTF_8))) {
            w.println(CSV_HEADER);
            for (int queue = 4; queue <= 32; queue += 4) {
                for (int rep = 0; rep < REPS_PER_POINT; rep++) {
                    long seed = mixSeed(CHANNELS, queue, meanIa, rep, 2);
                    writeOneRun(w, "by_queue", meanIa, CHANNELS, queue, rep, seed);
                }
            }
        }
    }

    private static long mixSeed(int channels, int queue, double meanIa, int rep, int salt) {
        long h = salt * 0x9E3779B97F4A7C15L;
        h ^= (long) channels << 32;
        h ^= queue;
        h ^= Double.doubleToRawLongBits(meanIa);
        h ^= (long) rep * 0x85EBCA6B;
        h *= 0xC2B2AE3D27D4EB4FL;
        return h == 0 ? 1L : h;
    }

    private static void writeOneRun(
            PrintWriter w,
            String sweep,
            double meanIaMs,
            int channels,
            int queue,
            int rep,
            long seed)
            throws Exception {
        SimulationConfig cfg =
                SimulationConfig.fromMillis(
                        channels,
                        queue,
                        meanIaMs,
                        SERV_MEAN_MS,
                        SERV_STD_MS,
                        MIN_SERVED,
                        SAMPLE_INTERVAL_MS,
                        seed);

        long t0 = System.nanoTime();
        SimulationResult r = new MultiChannelSmo(cfg).run();
        double wallS = (System.nanoTime() - t0) / 1_000_000_000.0;

        w.printf(
                "%s,%.4f,%d,%d,%d,%d,%.8f,%.8f,%d,%d,%d,%d,%.6f%n",
                sweep,
                meanIaMs,
                channels,
                queue,
                rep,
                seed,
                r.meanQueueLength(),
                r.rejectionProbability(),
                r.arrivalAttempts(),
                r.rejected(),
                r.served(),
                r.queueSampleCount(),
                wallS);
        w.flush();
    }
}
