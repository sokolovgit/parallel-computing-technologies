package mkr1.code;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * 
 * Напишіть фрагмент коду для пулу h потоків, що виконують паралельне обчислення
 * суми n елементів масиву дійсних чисел, розділяючи обчислення на m задач.
 * Організуйте завантаження задач колекцією. Забезпечте очікування на завершення
 * обчислень задач.
 * 
 */
public class Question15 {

    private static final int N = 1_000_000;
    private static final int H = 16;
    private static final int M = 100;

    public static void main(String[] args) throws InterruptedException {
        double[] array = new double[N];
        for (int i = 0; i < N; i++) {
            array[i] = Math.random();
        }

        BlockingQueue<Task> queue = new LinkedBlockingQueue<>();
        int chunk = N / M;
        for (int i = 0; i < M; i++) {
            int from = i * chunk;
            int to = (i == M - 1) ? N : from + chunk;
            queue.put(new Task(array, from, to));
        }

        double[] sharedSum = new double[] { 0 };
        Object lock = new Object();
        Thread[] workers = new Thread[H];

        for (int i = 0; i < H; i++) {
            workers[i] = new Thread(() -> {
                try {
                    while (true) {
                        Task task = queue.poll();
                        if (task == null) {
                            break;
                        }
                        double part = task.compute();
                        synchronized (lock) {
                            sharedSum[0] += part;
                        }
                    }
                } catch (Exception ignored) {
                }
            });
            workers[i].start();
        }

        for (Thread w : workers) {
            w.join();
        }

        System.out.println("Total sum: " + sharedSum[0]);
    }

    private record Task(double[] array, int from, int to) {
        double compute() {
            double sum = 0;
            for (int i = from; i < to; i++) {
                sum += array[i];
            }
            return sum;
        }
    }
}
