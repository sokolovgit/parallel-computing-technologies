package lab5.common;

import java.util.Random;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Random inter-arrival times (uniform with a given mean) and service times (normal, clamped).
 */
public final class Randoms {

    private Randoms() {}

    /**
     * Uniform inter-arrival on [0, 2*mean], so the expected value equals {@code mean}.
     */
    public static long nextInterArrivalNanos(Random rng, long meanInterArrivalNanos) {
        if (meanInterArrivalNanos < 1) {
            return 1;
        }
        double u = rng.nextDouble();
        long v = (long) (u * 2.0 * meanInterArrivalNanos);
        return Math.max(1L, v);
    }

    public static long nextServiceNanos(SimulationConfig cfg, Random rng) {
        double g = rng.nextGaussian();
        return clampServiceNanos(cfg, g);
    }

    /** For pool worker threads: {@link ThreadLocalRandom} (Java 8 TLR has no {@code nextGaussian}). */
    public static long nextServiceNanos(SimulationConfig cfg) {
        double g = nextGaussian(ThreadLocalRandom.current());
        return clampServiceNanos(cfg, g);
    }

    private static long clampServiceNanos(SimulationConfig cfg, double g) {
        long v = (long) (cfg.serviceMeanNanos() + g * cfg.serviceStdDevNanos());
        if (v < cfg.serviceMinNanos()) {
            v = cfg.serviceMinNanos();
        }
        if (v > cfg.serviceMaxNanos()) {
            v = cfg.serviceMaxNanos();
        }
        return v;
    }

    private static double nextGaussian(ThreadLocalRandom r) {
        double u1;
        do {
            u1 = r.nextDouble();
        } while (u1 <= 1e-12);
        double u2 = r.nextDouble();
        return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    }
}
