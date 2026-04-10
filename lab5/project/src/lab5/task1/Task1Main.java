package lab5.task1;

import lab5.common.SimulationConfig;
import lab5.common.SimulationResult;
import lab5.smo.MultiChannelSmo;

/**
 * Lab 5, part 1: single run of an N-server queueing model (thread pool = servers),
 * mean queue length and rejection probability.
 */
public final class Task1Main {

    private Task1Main() {}

    public static void main(String[] args) throws Exception {
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

        System.out.println("Parameters: channels=" + cfg.channels()
                + ", queueCapacity=" + cfg.queueCapacity()
                + ", minServed=" + cfg.minServed()
                + ", seed=" + cfg.randomSeed());

        MultiChannelSmo smo = new MultiChannelSmo(cfg);
        long t0 = System.nanoTime();
        SimulationResult r = smo.run();
        long dt = System.nanoTime() - t0;

        System.out.println(r);
        System.out.printf("Wall-clock run time: %.3f s%n", dt / 1_000_000_000.0);
    }
}
