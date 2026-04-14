package mkr2.java;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveTask;

public class task19 {

    public static void main(String[] args) {
        ArrayList<String> list = new ArrayList<>(Arrays.asList(
            "hello", "world", "fork", "join", "java", "parallel", "computing"
        ));

        try (ForkJoinPool pool = new ForkJoinPool()) {
            long[] result = pool.invoke(new WordLengthTask(list, 0, list.size()));
            double avg = result[1] == 0 ? 0 : (double) result[0] / result[1];
            System.out.println("Average word length = " + avg);
        }
    }

    static class WordLengthTask extends RecursiveTask<long[]> {
        private final ArrayList<String> list;
        private final int from, to;
        private static final int THRESHOLD = 100;

        WordLengthTask(ArrayList<String> list, int from, int to) {
            this.list = list;
            this.from = from;
            this.to = to;
        }

        @Override
        protected long[] compute() {
            int n = to - from;
            if (n <= THRESHOLD) {
                long total = 0;
                for (int i = from; i < to; i++) {
                    total += list.get(i).length();
                }
                return new long[] { total, n };
            }
            int mid = from + n / 2;
            WordLengthTask left = new WordLengthTask(list, from, mid);
            WordLengthTask right = new WordLengthTask(list, mid, to);
            left.fork();
            long[] r = right.compute();
            long[] l = left.join();
            return new long[] { l[0] + r[0], l[1] + r[1] };
        }
    }
}
