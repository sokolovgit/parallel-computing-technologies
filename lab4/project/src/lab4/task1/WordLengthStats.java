package lab4.task1;

import java.util.Arrays;

/** Mergeable statistics for the random variable "word length (characters)". */
public final class WordLengthStats {

    /** Buckets for lengths 1..(BUCKETS-1); last bucket aggregates length >= BUCKETS. */
    public static final int BUCKETS = 65;

    private final long[] histogram;
    private long wordCount;
    private long sumLengths;
    private long sumSqLengths;

    public WordLengthStats() {
        this.histogram = new long[BUCKETS];
    }

    public void addWord(int length) {
        if (length <= 0) {
            return;
        }
        int idx = length < BUCKETS ? length - 1 : BUCKETS - 1;
        histogram[idx]++;
        wordCount++;
        sumLengths += length;
        sumSqLengths += (long) length * length;
    }

    public void merge(WordLengthStats other) {
        for (int i = 0; i < BUCKETS; i++) {
            histogram[i] += other.histogram[i];
        }
        wordCount += other.wordCount;
        sumLengths += other.sumLengths;
        sumSqLengths += other.sumSqLengths;
    }

    public long wordCount() {
        return wordCount;
    }

    /** Population mean E[X]. */
    public double mean() {
        if (wordCount == 0) {
            return Double.NaN;
        }
        return (double) sumLengths / wordCount;
    }

    /** Population standard deviation sqrt(E[X^2] - E[X]^2). */
    public double standardDeviation() {
        if (wordCount == 0) {
            return Double.NaN;
        }
        double m = mean();
        double meanSq = (double) sumSqLengths / wordCount;
        double v = meanSq - m * m;
        return v > 0 ? Math.sqrt(v) : 0.0;
    }

    public long[] histogramCopy() {
        return Arrays.copyOf(histogram, BUCKETS);
    }

    public static WordLengthStats merge(WordLengthStats a, WordLengthStats b) {
        WordLengthStats out = new WordLengthStats();
        out.merge(a);
        out.merge(b);
        return out;
    }
}
