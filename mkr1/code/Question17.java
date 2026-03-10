package mkr1.code;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

/**
 *
 * Напишіть фрагмент коду, в якому створюються та запускаються на виконання
 * потоки А,В,С. Потоки А і В виконують створення та додавання об’єктів в буфер
 * обмеженої довжини, а потік С – їх вилучення. Використовуйте тип Object для
 * об'єктів, які створюються, додаються та вилучаються.
 * 
 */

public class Question17 {

    private static final int BUFFER_CAPACITY = 5;
    private static final int ITEMS_PER_PRODUCER = 4;

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Object> buffer = new ArrayBlockingQueue<>(BUFFER_CAPACITY);

        Thread threadA = new Thread(() -> produce(buffer, "A"));
        Thread threadB = new Thread(() -> produce(buffer, "B"));
        Thread threadC = new Thread(() -> consume(buffer));

        threadA.start();
        threadB.start();
        threadC.start();

        threadA.join();
        threadB.join();
        threadC.join();
        System.out.println("Done.");
    }

    private static void produce(BlockingQueue<Object> buffer, String name) {
        try {
            for (int i = 0; i < ITEMS_PER_PRODUCER; i++) {
                buffer.put(new Object());
                System.out.println(name + " put, size=" + buffer.size());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void consume(BlockingQueue<Object> buffer) {
        try {
            for (int i = 0; i < ITEMS_PER_PRODUCER * 2; i++) {
                buffer.take();
                System.out.println("C take, size=" + buffer.size());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
