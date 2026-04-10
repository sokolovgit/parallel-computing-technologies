package lab5.common;

/**
 * Outcome of one run: mean queue length (from discrete samples) and rejection probability.
 */
public final class SimulationResult {

    private final double meanQueueLength;
    private final double rejectionProbability;
    private final long arrivalAttempts;
    private final long rejected;
    private final long served;
    private final long queueSampleCount;

    public SimulationResult(
            double meanQueueLength,
            double rejectionProbability,
            long arrivalAttempts,
            long rejected,
            long served,
            long queueSampleCount) {
        this.meanQueueLength = meanQueueLength;
        this.rejectionProbability = rejectionProbability;
        this.arrivalAttempts = arrivalAttempts;
        this.rejected = rejected;
        this.served = served;
        this.queueSampleCount = queueSampleCount;
    }

    public double meanQueueLength() {
        return meanQueueLength;
    }

    public double rejectionProbability() {
        return rejectionProbability;
    }

    public long arrivalAttempts() {
        return arrivalAttempts;
    }

    public long rejected() {
        return rejected;
    }

    public long served() {
        return served;
    }

    public long queueSampleCount() {
        return queueSampleCount;
    }

    @Override
    public String toString() {
        return String.format(
                "SimulationResult{meanQueue=%.4f, P_reject=%.6f, arrivals=%d, rejected=%d, served=%d, samples=%d}",
                meanQueueLength,
                rejectionProbability,
                arrivalAttempts,
                rejected,
                served,
                queueSampleCount);
    }
}
