package results;

/** One row of exported benchmark output. */
public final class BenchmarkResult {

    public final String algorithm;
    public final int n;
    public final int threads;
    public final Integer q;
    public final double tParallelMs;
    public final double tSequentialMs;
    public final double speedup;
    public final String jvm;
    public final String os;
    public final String hostname;

    public BenchmarkResult(
            String algorithm,
            int n,
            int threads,
            Integer q,
            double tParallelMs,
            double tSequentialMs,
            double speedup,
            String jvm,
            String os,
            String hostname) {
        this.algorithm = algorithm;
        this.n = n;
        this.threads = threads;
        this.q = q;
        this.tParallelMs = tParallelMs;
        this.tSequentialMs = tSequentialMs;
        this.speedup = speedup;
        this.jvm = jvm;
        this.os = os;
        this.hostname = hostname;
    }
}
