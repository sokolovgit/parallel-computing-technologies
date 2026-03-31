package io;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Locale;
import results.BenchmarkResult;

public final class ResultsExporter {

    private ResultsExporter() {}

    public static void writeCsv(Path path, List<BenchmarkResult> rows) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append(
                "algorithm,n,threads,q,t_parallel_ms,t_sequential_ms,speedup,jvm,os,hostname,timestamp\n");
        String ts = Instant.now().toString();
        for (BenchmarkResult r : rows) {
            sb.append(r.algorithm)
                    .append(',')
                    .append(r.n)
                    .append(',')
                    .append(r.threads)
                    .append(',')
                    .append(r.q == null ? "" : r.q)
                    .append(',')
                    .append(String.format(Locale.US, "%.6f", r.tParallelMs))
                    .append(',')
                    .append(String.format(Locale.US, "%.6f", r.tSequentialMs))
                    .append(',')
                    .append(String.format(Locale.US, "%.6f", r.speedup))
                    .append(',')
                    .append(escapeCsv(jvmShort(r.jvm)))
                    .append(',')
                    .append(escapeCsv(r.os))
                    .append(',')
                    .append(escapeCsv(r.hostname))
                    .append(',')
                    .append(ts)
                    .append('\n');
        }
        Files.writeString(path, sb.toString(), StandardCharsets.UTF_8);
    }

    private static String jvmShort(String jvm) {
        return jvm.replace('\n', ' ');
    }

    private static String escapeCsv(String s) {
        if (s.indexOf(',') < 0 && s.indexOf('"') < 0) {
            return s;
        }
        return '"' + s.replace("\"", "\"\"") + '"';
    }
}
