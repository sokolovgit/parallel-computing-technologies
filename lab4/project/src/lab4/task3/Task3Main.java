package lab4.task3;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ForkJoinPool;
import java.util.stream.Stream;

/**
 * Завдання 3: слова, спільні для всіх текстових документів у каталозі, через ForkJoin (перетин множин).
 */
public final class Task3Main {

    private static final Path DATA_DIR = Paths.get("data/task3");

    public static void main(String[] args) {
        Path base = Paths.get(System.getProperty("lab4.home", ".")).normalize();
        String mode = args.length == 0 ? "demo" : args[0];
        if (!"demo".equals(mode)) {
            System.err.println("Usage: Task3Main [demo]");
            System.exit(1);
        }
        runDemo(base);
    }

    private static void runDemo(Path base) {
        List<Path> files = listTxtFiles(base.resolve(DATA_DIR));
        if (files.isEmpty()) {
            System.err.println("No .txt under " + base.resolve(DATA_DIR));
            System.exit(1);
        }

        Set<String> seq = sequentialCommon(files);
        int p = Runtime.getRuntime().availableProcessors();
        Set<String> par;
        try (ForkJoinPool pool = new ForkJoinPool(p)) {
            CommonWordsTask task = new CommonWordsTask(files, 0, files.size());
            par = pool.invoke(task);
        }

        if (!seq.equals(par)) {
            System.err.println("Mismatch: sequential size " + seq.size() + ", parallel " + par.size());
            System.exit(1);
        }

        System.out.println("Files: " + files.size() + ", common distinct words: " + par.size());
        System.out.println("ForkJoinPool parallelism: " + p);
        List<String> sample = new ArrayList<>(par);
        Collections.sort(sample);
        int show = Math.min(40, sample.size());
        System.out.println("Sample (" + show + " / " + sample.size() + "):");
        for (int i = 0; i < show; i++) {
            System.out.println("  " + sample.get(i));
        }
    }

    private static List<Path> listTxtFiles(Path root) {
        List<Path> out = new ArrayList<>();
        if (!Files.isDirectory(root)) {
            return out;
        }
        try (Stream<Path> walk = Files.walk(root)) {
            walk.filter(p -> Files.isRegularFile(p) && p.toString().toLowerCase(Locale.ROOT).endsWith(".txt"))
                    .forEach(out::add);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        Collections.sort(out);
        return out;
    }

    static Set<String> sequentialCommon(List<Path> files) {
        if (files.isEmpty()) {
            return Set.of();
        }
        Set<String> acc = new java.util.HashSet<>(CommonWordsTask.readWords(files.get(0)));
        for (int i = 1; i < files.size(); i++) {
            acc.retainAll(CommonWordsTask.readWords(files.get(i)));
            if (acc.isEmpty()) {
                break;
            }
        }
        return acc;
    }
}
