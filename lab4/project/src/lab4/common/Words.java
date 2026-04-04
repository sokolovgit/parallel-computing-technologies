package lab4.common;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.function.Consumer;
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

    /** Lowercase word tokens (same class as {@link #forEachWordLength}). */
    public static void forEachWord(String line, Consumer<String> onWord) {
        if (line == null || line.isEmpty()) {
            return;
        }
        Matcher m = TOKEN.matcher(line);
        while (m.find()) {
            onWord.accept(m.group().toLowerCase(Locale.ROOT));
        }
    }

    /** Усі різні слова з UTF-8 текстового файлу (нижній регістр). */
    public static Set<String> readWordSet(Path path) {
        try {
            HashSet<String> s = new HashSet<>();
            for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
                forEachWord(line, s::add);
            }
            return s;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
