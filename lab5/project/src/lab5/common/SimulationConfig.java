package lab5.common;

/**
 * Parameters for one simulation run of a multi-server queueing system with a finite buffer.
 */
public final class SimulationConfig {

    private final int channels;
    private final int queueCapacity;
    /** Mean inter-arrival time (ns); implemented as Uniform[0, 2*mean] so E[interval] = mean. */
    private final long meanInterArrivalNanos;
    /** Normal service-time parameters (ns); values are clamped to a positive range. */
    private final long serviceMeanNanos;
    private final long serviceStdDevNanos;
    private final long serviceMinNanos;
    private final long serviceMaxNanos;
    /** Minimum number of served customers before stopping the run (lab spec: at least 1000). */
    private final int minServed;
    /** Queue-length sampling period (ms), observed in a dedicated thread. */
    private final long queueSampleIntervalMillis;
    private final long randomSeed;

    public SimulationConfig(
            int channels,
            int queueCapacity,
            long meanInterArrivalNanos,
            long serviceMeanNanos,
            long serviceStdDevNanos,
            long serviceMinNanos,
            long serviceMaxNanos,
            int minServed,
            long queueSampleIntervalMillis,
            long randomSeed) {
        if (channels < 1) {
            throw new IllegalArgumentException("channels must be >= 1");
        }
        if (queueCapacity < 0) {
            throw new IllegalArgumentException("queueCapacity must be >= 0");
        }
        if (meanInterArrivalNanos < 1) {
            throw new IllegalArgumentException("meanInterArrivalNanos must be >= 1");
        }
        if (minServed < 1) {
            throw new IllegalArgumentException("minServed must be >= 1");
        }
        if (queueSampleIntervalMillis < 1) {
            throw new IllegalArgumentException("queueSampleIntervalMillis must be >= 1");
        }
        this.channels = channels;
        this.queueCapacity = queueCapacity;
        this.meanInterArrivalNanos = meanInterArrivalNanos;
        this.serviceMeanNanos = serviceMeanNanos;
        this.serviceStdDevNanos = serviceStdDevNanos;
        this.serviceMinNanos = serviceMinNanos;
        this.serviceMaxNanos = serviceMaxNanos;
        this.minServed = minServed;
        this.queueSampleIntervalMillis = queueSampleIntervalMillis;
        this.randomSeed = randomSeed;
    }

    /** Factory that takes times in milliseconds and converts them to nanoseconds. */
    public static SimulationConfig fromMillis(
            int channels,
            int queueCapacity,
            double meanInterArrivalMs,
            double serviceMeanMs,
            double serviceStdDevMs,
            int minServed,
            long queueSampleIntervalMillis,
            long randomSeed) {
        long msToNs = 1_000_000L;
        return new SimulationConfig(
                channels,
                queueCapacity,
                Math.max(1L, (long) (meanInterArrivalMs * msToNs)),
                (long) (serviceMeanMs * msToNs),
                Math.max(1L, (long) (serviceStdDevMs * msToNs)),
                1L,
                Math.max(1L, (long) (serviceMeanMs * 5 * msToNs)),
                minServed,
                queueSampleIntervalMillis,
                randomSeed);
    }

    public int channels() {
        return channels;
    }

    public int queueCapacity() {
        return queueCapacity;
    }

    public long meanInterArrivalNanos() {
        return meanInterArrivalNanos;
    }

    public long serviceMeanNanos() {
        return serviceMeanNanos;
    }

    public long serviceStdDevNanos() {
        return serviceStdDevNanos;
    }

    public long serviceMinNanos() {
        return serviceMinNanos;
    }

    public long serviceMaxNanos() {
        return serviceMaxNanos;
    }

    public int minServed() {
        return minServed;
    }

    public long queueSampleIntervalMillis() {
        return queueSampleIntervalMillis;
    }

    public long randomSeed() {
        return randomSeed;
    }
}
