package config;

import java.nio.file.Path;

public final class BenchmarkConfig {

    private static final int DEFAULT_RUNS = 20;

    public final int[] sizes;
    public final int[] threads;
    public final int runs;
    public final Path outDir;
    public final String prefix;
    public final boolean striped;
    public final boolean fox;
    public final boolean verify;

    public BenchmarkConfig(
            int[] sizes,
            int[] threads,
            int runs,
            Path outDir,
            String prefix,
            boolean striped,
            boolean fox,
            boolean verify) {
        this.sizes = sizes;
        this.threads = threads;
        this.runs = runs;
        this.outDir = outDir;
        this.prefix = prefix;
        this.striped = striped;
        this.fox = fox;
        this.verify = verify;
    }

    public static BenchmarkConfig parse(String[] args) {
        int[] sizes = {512, 1024};
        int[] threads = {4, 9, 16};
        int runs = DEFAULT_RUNS;
        Path out = defaultOutDir();
        String prefix = "benchmark";
        boolean striped = true;
        boolean fox = true;
        boolean verify = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--verify":
                    verify = true;
                    break;
                case "--sizes":
                    sizes = parseInts(require(args, ++i, args.length));
                    break;
                case "--threads":
                    threads = parseInts(require(args, ++i, args.length));
                    break;
                case "--runs":
                    runs = Integer.parseInt(require(args, ++i, args.length));
                    break;
                case "--out":
                    out = Path.of(require(args, ++i, args.length));
                    break;
                case "--prefix":
                    prefix = require(args, ++i, args.length);
                    break;
                case "--algorithms":
                    String algs = require(args, ++i, args.length);
                    striped = algs.contains("striped") || algs.contains("both");
                    fox = algs.contains("fox") || algs.contains("both");
                    break;
                default:
                    throw new IllegalArgumentException("Unknown arg: " + args[i]);
            }
        }
        return new BenchmarkConfig(sizes, threads, runs, out, prefix, striped, fox, verify);
    }

    /**
     * Default is {@code ./results} from the JVM working directory. When {@code -Dmatmul.home=DIR} is set
     * (the {@code just} recipes set it to the project root), output goes to {@code DIR/results} so it stays
     * next to {@code matmul/} and {@code plots/}.
     */
    private static Path defaultOutDir() {
        String home = System.getProperty("matmul.home");
        if (home != null && !home.isEmpty()) {
            return Path.of(home).resolve("results");
        }
        return Path.of("results");
    }

    static String require(String[] args, int i, int len) {
        if (i >= len) {
            throw new IllegalArgumentException("Missing value");
        }
        return args[i];
    }

    static int[] parseInts(String s) {
        String[] parts = s.split(",");
        int[] out = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            out[i] = Integer.parseInt(parts[i].trim());
        }
        return out;
    }
}
