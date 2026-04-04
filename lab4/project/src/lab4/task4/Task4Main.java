package lab4.task4;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ForkJoinPool;
import java.util.stream.Stream;
import lab4.common.Words;

/**
 * Завдання 4: пошук .txt документів, що відповідають набору ІТ-ключових слів (fork/join по списку файлів).
 */
public final class Task4Main {

    private static final Path DATA_DIR = Paths.get("data/task4");

    public static void main(String[] args) {
        Path base = Paths.get(System.getProperty("lab4.home", ".")).normalize();
        String mode = args.length == 0 ? "demo" : args[0];
        if (!"demo".equals(mode)) {
            System.err.println("Usage: Task4Main [demo]");
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

        List<Path> seq = sequentialMatches(files);
        int p = Runtime.getRuntime().availableProcessors();
        List<Path> par;
        try (ForkJoinPool pool = new ForkJoinPool(p)) {
            KeywordSearchTask task = new KeywordSearchTask(files, 0, files.size());
            par = pool.invoke(task);
        }

        Collections.sort(seq);
        if (!seq.equals(par)) {
            System.err.println("Mismatch sequential vs parallel.");
            System.err.println("seq: " + seq);
            System.err.println("par: " + par);
            System.exit(1);
        }

        List<String> kwPreview = new ArrayList<>(KeywordSearchTask.IT_KEYWORDS);
        Collections.sort(kwPreview);
        int showKw = Math.min(10, kwPreview.size());
        System.out.println(
                "IT keyword set (total " + kwPreview.size() + ", show " + showKw + "): "
                        + kwPreview.subList(0, showKw));
        System.out.println(
                "Rule: at least " + KeywordSearchTask.MIN_KEYWORD_HITS + " distinct keywords as word tokens.");
        System.out.println("Files scanned: " + files.size() + ", matches: " + par.size() + ", pool P=" + p);
        for (Path path : par) {
            int hits = KeywordSearchTask.countKeywordHits(Words.readWordSet(path));
            System.out.println("  " + path.getFileName() + " (" + hits + " keyword hits)");
        }
    }

    private static List<Path> listTxtFiles(Path root) {
        List<Path> out = new ArrayList<>();
        if (!Files.isDirectory(root)) {
            return out;
        }
        try (Stream<Path> walk = Files.walk(root)) {
            walk.filter(x -> Files.isRegularFile(x) && x.toString().toLowerCase(Locale.ROOT).endsWith(".txt"))
                    .forEach(out::add);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        Collections.sort(out);
        return out;
    }

    static List<Path> sequentialMatches(List<Path> files) {
        List<Path> out = new ArrayList<>();
        for (Path path : files) {
            if (KeywordSearchTask.matches(Words.readWordSet(path))) {
                out.add(path);
            }
        }
        return out;
    }
}
