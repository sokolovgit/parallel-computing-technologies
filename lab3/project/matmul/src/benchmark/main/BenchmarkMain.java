package main;

import config.BenchmarkConfig;
import runner.BenchmarkRunner;

/**
 * CLI: benchmark striped and Fox multiplies; export CSV. Protocol per lab task: warmup sequential
 * &times;1, then timed parallel runs, then timed sequential runs (per configuration).
 */
public final class BenchmarkMain {

    private BenchmarkMain() {}

    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            printUsage();
            return;
        }
        BenchmarkConfig cfg = BenchmarkConfig.parse(args);
        if (cfg.verify) {
            BenchmarkRunner.runVerification();
            return;
        }
        BenchmarkRunner.runBenchmark(cfg);
    }

    private static void printUsage() {
        System.err.println(
                "Usage: BenchmarkMain --verify | [options]\n"
                        + "  --sizes n1,n2,...     matrix dimensions (default 512,1024)\n"
                        + "  --threads t1,t2,...   thread counts for striped (default 4,9,16)\n"
                        + "  --runs N              timed runs per phase (default 20)\n"
                        + "  --out DIR             output directory (default: ./results, or <matmul.home>/results if set)\n"
                        + "  --prefix NAME         file name prefix (default benchmark)\n"
                        + "  --algorithms sequential|striped|fox|both|all  (default both; all = sequential+striped+fox)\n"
                        + "  --verify              correctness check only\n");
    }
}
