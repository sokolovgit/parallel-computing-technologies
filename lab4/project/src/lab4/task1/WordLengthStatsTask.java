package lab4.task1;

import java.util.concurrent.RecursiveTask;
import lab4.common.Words;

/** ForkJoin: split line range; merge {@link WordLengthStats} from children. */
public final class WordLengthStatsTask extends RecursiveTask<WordLengthStats> {

    private final String[] lines;
    private final int from;
    private final int to;
    private final int lineThreshold;

    public WordLengthStatsTask(String[] lines, int from, int to, int lineThreshold) {
        this.lines = lines;
        this.from = from;
        this.to = to;
        this.lineThreshold = lineThreshold;
    }

    @Override
    protected WordLengthStats compute() {
        int n = to - from;
        if (n <= lineThreshold) {
            WordLengthStats acc = new WordLengthStats();
            for (int i = from; i < to; i++) {
                Words.forEachWordLength(lines[i], acc::addWord);
            }
            return acc;
        }
        int mid = from + n / 2;
        WordLengthStatsTask left = new WordLengthStatsTask(lines, from, mid, lineThreshold);
        WordLengthStatsTask right = new WordLengthStatsTask(lines, mid, to, lineThreshold);
        left.fork();
        WordLengthStats r = right.compute();
        WordLengthStats l = left.join();
        l.merge(r);
        return l;
    }
}
