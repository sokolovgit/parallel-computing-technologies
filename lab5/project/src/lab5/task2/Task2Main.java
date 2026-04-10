package lab5.task2;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import lab5.common.SimulationConfig;
import lab5.common.SimulationResult;
import lab5.smo.MultiChannelSmo;

/**
 * Lab 5, part 2: run several independent SMO simulations in parallel (separate {@link MultiChannelSmo}
 * per replication, distinct seeds) and aggregate mean queue length and rejection probability.
 */
public final class Task2Main {

    private static final int MIN_RUNS = 4;
    private static final int DEFAULT_RUNS = 8;
    private static final long BASE_SEED = 42L;

    private Task2Main() {}

    public static void main(String[] args) throws Exception {
        int runs = parseRuns(args);
        boolean verbose = hasFlag(args, "-v", "--verbose");

        int channels = 4;
        int queueCapacity = 8;
        double meanIaMs = 0.08;
        double servMeanMs = 0.25;
        double servStdMs = 0.06;
        int minServed = 1000;
        long sampleIntervalMs = 2L;

        int cores = Runtime.getRuntime().availableProcessors();
        int poolSize = Math.max(1, Math.min(runs, cores));

        System.out.println("Task 2: parallel independent runs (lab spec: at least " + MIN_RUNS + ").");
        System.out.println("Parameters: channels=" + channels + ", queueCapacity=" + queueCapacity
                + ", meanIA_ms=" + meanIaMs + ", minServed=" + minServed + ", parallelRuns=" + runs
                + ", outerPoolThreads=" + poolSize);

        List<Callable<SimulationResult>> tasks = new ArrayList<>();
        for (int i = 0; i < runs; i++) {
            final long seed = BASE_SEED + (long) i * 0x9E3779B97F4A7C15L;
            tasks.add(
                    () -> {
                        SimulationConfig cfg =
                                SimulationConfig.fromMillis(
                                        channels,
                                        queueCapacity,
                                        meanIaMs,
                                        servMeanMs,
                                        servStdMs,
                                        minServed,
                                        sampleIntervalMs,
                                        seed);
                        return new MultiChannelSmo(cfg).run();
                    });
        }

        ExecutorService outer = Executors.newFixedThreadPool(poolSize);
        long t0 = System.nanoTime();
        List<Future<SimulationResult>> futures;
        try {
            futures = outer.invokeAll(tasks);
        } finally {
            outer.shutdown();
            if (!outer.awaitTermination(30, TimeUnit.MINUTES)) {
                outer.shutdownNow();
            }
        }
        long wallNs = System.nanoTime() - t0;

        double[] meanQueues = new double[runs];
        double[] pRejects = new double[runs];
        for (int i = 0; i < runs; i++) {
            try {
                SimulationResult r = futures.get(i).get();
                meanQueues[i] = r.meanQueueLength();
                pRejects[i] = r.rejectionProbability();
                if (verbose) {
                    System.out.println("run " + i + " seed=" + (BASE_SEED + (long) i * 0x9E3779B97F4A7C15L) + " -> " + r);
                }
            } catch (ExecutionException e) {
                Throwable c = e.getCause() != null ? e.getCause() : e;
                throw new RuntimeException("run " + i + " failed: " + c.getMessage(), c);
            }
        }

        double mqMean = mean(meanQueues);
        double mqStd = sampleStdDev(meanQueues);
        double prMean = mean(pRejects);
        double prStd = sampleStdDev(pRejects);

        System.out.println();
        System.out.printf("Aggregated mean queue length (over %d runs): %.6f (sample stdev %.6f)%n", runs, mqMean, mqStd);
        System.out.printf("Aggregated rejection probability (over %d runs): %.6f (sample stdev %.6f)%n", runs, prMean, prStd);
        System.out.printf("Total wall-clock time (all runs, parallel): %.3f s%n", wallNs / 1_000_000_000.0);
    }

    private static int parseRuns(String[] args) {
        for (String a : args) {
            if (a.startsWith("-")) {
                continue;
            }
            try {
                int n = Integer.parseInt(a);
                if (n < MIN_RUNS) {
                    System.err.println("runs must be >= " + MIN_RUNS + ", using " + MIN_RUNS);
                    return MIN_RUNS;
                }
                return n;
            } catch (NumberFormatException ignored) {
                System.err.println("Ignoring non-integer argument: " + a);
            }
        }
        return DEFAULT_RUNS;
    }

    private static boolean hasFlag(String[] args, String... flags) {
        for (String a : args) {
            for (String f : flags) {
                if (f.equals(a)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static double mean(double[] xs) {
        double s = 0.0;
        for (double x : xs) {
            s += x;
        }
        return s / xs.length;
    }

    /** Bessel-corrected sample standard deviation; returns 0 if there are fewer than two samples. */
    private static double sampleStdDev(double[] xs) {
        if (xs.length < 2) {
            return 0.0;
        }
        double m = mean(xs);
        double acc = 0.0;
        for (double x : xs) {
            double d = x - m;
            acc += d * d;
        }
        return Math.sqrt(acc / (xs.length - 1));
    }
}
