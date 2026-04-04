package lab4.task3;

import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.RecursiveTask;
import lab4.common.Words;

/**
 * Перетин множин слів по документах: рекурсивно ділить список файлів, у листі читає один файл;
 * внутрішні вузли повертають перетин множин зліва й справа.
 */
public final class CommonWordsTask extends RecursiveTask<Set<String>> {

    private final List<Path> files;
    private final int from;
    private final int to;

    public CommonWordsTask(List<Path> files, int from, int to) {
        this.files = files;
        this.from = from;
        this.to = to;
    }

    @Override
    protected Set<String> compute() {
        int span = to - from;
        if (span <= 0) {
            return Set.of();
        }
        if (span == 1) {
            return readWords(files.get(from));
        }
        int mid = from + span / 2;
        CommonWordsTask left = new CommonWordsTask(files, from, mid);
        CommonWordsTask right = new CommonWordsTask(files, mid, to);
        left.fork();
        Set<String> r = right.compute();
        Set<String> l = left.join();
        return intersect(l, r);
    }

    static Set<String> intersect(Set<String> a, Set<String> b) {
        if (a.isEmpty() || b.isEmpty()) {
            return Set.of();
        }
        if (a.size() <= b.size()) {
            HashSet<String> out = new HashSet<>(a);
            out.retainAll(b);
            return out;
        }
        HashSet<String> out = new HashSet<>(b);
        out.retainAll(a);
        return out;
    }

    static Set<String> readWords(Path p) {
        return Words.readWordSet(p);
    }
}
