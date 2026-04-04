package lab4.task4;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.RecursiveTask;
import lab4.common.Words;

/**
 * Паралельний відбір файлів, у тексті яких зустрічається достатньо ключових слів з предметної області ІТ.
 */
public final class KeywordSearchTask extends RecursiveTask<List<Path>> {

    /** Ключові слова (нижній регістр), область «інформаційні технології». */
    static final Set<String> IT_KEYWORDS =
            Set.of(
                    "java",
                    "python",
                    "algorithm",
                    "database",
                    "network",
                    "thread",
                    "server",
                    "client",
                    "cloud",
                    "api",
                    "software",
                    "hardware",
                    "cpu",
                    "memory",
                    "cache",
                    "compiler",
                    "debug",
                    "repository",
                    "kubernetes",
                    "docker",
                    "linux",
                    "encryption",
                    "protocol");

    /** Мінімальна кількість різних ключових слів як цілих токенів у документі. */
    static final int MIN_KEYWORD_HITS = 2;

    private final List<Path> files;
    private final int from;
    private final int to;

    public KeywordSearchTask(List<Path> files, int from, int to) {
        this.files = files;
        this.from = from;
        this.to = to;
    }

    @Override
    protected List<Path> compute() {
        int span = to - from;
        if (span <= 0) {
            return List.of();
        }
        if (span == 1) {
            Path p = files.get(from);
            Set<String> words = Words.readWordSet(p);
            if (countKeywordHits(words) >= MIN_KEYWORD_HITS) {
                return List.of(p);
            }
            return List.of();
        }
        int mid = from + span / 2;
        KeywordSearchTask left = new KeywordSearchTask(files, from, mid);
        KeywordSearchTask right = new KeywordSearchTask(files, mid, to);
        left.fork();
        List<Path> r = right.compute();
        List<Path> l = left.join();
        ArrayList<Path> out = new ArrayList<>(l.size() + r.size());
        out.addAll(l);
        out.addAll(r);
        Collections.sort(out);
        return out;
    }

    static int countKeywordHits(Set<String> docWords) {
        int n = 0;
        for (String kw : IT_KEYWORDS) {
            if (docWords.contains(kw)) {
                n++;
            }
        }
        return n;
    }

    static boolean matches(Set<String> docWords) {
        return countKeywordHits(docWords) >= MIN_KEYWORD_HITS;
    }
}
