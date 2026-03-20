package mkr1.code;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Напишіть фрагмент коду багатопотокової програми, в якій 7 потоків виконують
 * ітерації, в кожній з яких створюють об'єкт String з випадковим набором
 * символів та одразу додають його у спільну для всіх потоків колекцію об'єктів
 * String. Кількість символів у генерованому "слові" визначається
 * ідентифікатором потоку так, що потік генерує слово довжиною id+1 символ.
 * Додавання елементів відбувається допоки розмір колекції не досягне значення
 * 10000 елементів.
 */
public class Question8 {

    private static final int THREAD_COUNT = 7;
    private static final int TARGET_SIZE = 10_000;
    private static final List<String> sharedStrings = Collections.synchronizedList(new ArrayList<>());

    public static void main(String[] args) throws InterruptedException {
        Thread[] threads = new Thread[THREAD_COUNT];

        for (int id = 0; id < THREAD_COUNT; id++) {
            int threadId = id;
            threads[id] = new Thread(() -> runGenerator(threadId));
            threads[id].start();
        }

        for (Thread t : threads) {
            t.join();
        }

        System.out.println("Collection size: " + sharedStrings.size());
    }

    private static void runGenerator(int threadId) {
        Random random = new Random();
        int wordLength = threadId + 1;

        while (true) {
            String word = randomString(random, wordLength);
            synchronized (sharedStrings) {
                if (sharedStrings.size() >= TARGET_SIZE) {
                    break;
                }
                sharedStrings.add(word);
            }
        }
    }

    private static String randomString(Random random, int length) {
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append((char) ('a' + random.nextInt(26)));
        }
        return sb.toString();
    }
}
