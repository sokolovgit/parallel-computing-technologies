package lab4.common;

import java.util.function.IntConsumer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Tokenization helpers shared across lab4 tasks. */
public final class Words {

    private static final Pattern TOKEN = Pattern.compile("[\\p{L}\\p{M}\\p{N}]+");

    private Words() {}

    /** Invokes {@code onLength} for each word length in the line (Unicode letters, marks, numbers). */
    public static void forEachWordLength(String line, IntConsumer onLength) {
        if (line == null || line.isEmpty()) {
            return;
        }
        Matcher m = TOKEN.matcher(line);
        while (m.find()) {
            onLength.accept(m.group().length());
        }
    }
}
