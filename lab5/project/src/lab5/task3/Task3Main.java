package lab5.task3;

import lab5.common.SimulationConfig;
import lab5.common.SimulationResult;
import lab5.smo.MultiChannelSmo;

/**
 * Lab 5, part 3: run the SMO while a separate {@code status-reporter} thread periodically prints queue
 * depth, busy servers, and counters ({@link MultiChannelSmo#runWithLiveReporter(long)}).
 */
public final class Task3Main {

    /** Default tick so a ~0.1–0.2 s run still prints at least one status line on typical hardware. */
    private static final long DEFAULT_REPORT_MS = 100L;
    private static final long MIN_REPORT_MS = 1L;

    private Task3Main() {}

    public static void main(String[] args) throws Exception {
        long reportMs = DEFAULT_REPORT_MS;
        for (String a : args) {
            if (a.startsWith("-")) {
                continue;
            }
            try {
                long v = Long.parseLong(a);
                reportMs = Math.max(MIN_REPORT_MS, v);
            } catch (NumberFormatException e) {
                System.err.println("Ignoring non-numeric argument: " + a);
            }
        }

        SimulationConfig cfg =
                SimulationConfig.fromMillis(
                        4,
                        8,
                        0.08,
                        0.25,
                        0.06,
                        1000,
                        2L,
                        42L);

        System.out.println("Task 3: simulation in worker threads; status lines from a separate reporter thread.");
        System.out.println("Parameters: channels=" + cfg.channels()
                + ", queueCapacity=" + cfg.queueCapacity()
                + ", minServed=" + cfg.minServed()
                + ", seed=" + cfg.randomSeed()
                + ", reporterIntervalMs=" + reportMs);

        MultiChannelSmo smo = new MultiChannelSmo(cfg);
        long t0 = System.nanoTime();
        SimulationResult r = smo.runWithLiveReporter(reportMs);
        long dt = System.nanoTime() - t0;

        System.out.println("--- final result ---");
        System.out.println(r);
        System.out.printf("Wall-clock run time: %.3f s%n", dt / 1_000_000_000.0);
    }
}
