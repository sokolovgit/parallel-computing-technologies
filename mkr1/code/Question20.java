package mkr1.code;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Напишіть потік «Автівки», в якому автівки з черги виконують метод go() з
 * затримкою 2 мілісекунд за умови, що у потоці «Світлофор» встановлений сигнал
 * «зелене світло», і знову повторюють цю дію через 400 мілісекунд. «Світлофор»
 * змінює сигнали «зелене» «жовте» «червоне» «жовте» (і знову «зелене») циклічно
 * з затримками 70, 10, 40, 10 мілісекунд відповідно. При зеленому світлі
 * автівки проїжджають по одній. Створіть два потоки «Автівки» та один потік
 * «Світлофор» так, щоб один з потоків "Автівки" отримував дозвіл на переїзд за
 * умови "зеленого" сигналу, а другий - за умови "червоного" сигналу. Запустіть
 * потоки на виконання. Після проїзду 10000 автівок через світлофор завершіть
 * роботу потоків.
 */
public class Question20 {

    private static final int TARGET_PASSED = 10_000;
    private static final int GO_DELAY_MS = 2;
    private static final int CAR_REPEAT_MS = 400;
    private static final int GREEN_MS = 70;
    private static final int YELLOW_MS = 10;
    private static final int RED_MS = 40;

    private static volatile Signal signal = Signal.GREEN;
    private static volatile boolean stop = false;
    private static final AtomicInteger passedCount = new AtomicInteger(0);

    enum Signal {
        GREEN, YELLOW, RED
    }

    public static void main(String[] args) throws InterruptedException {
        Thread trafficLight = new Thread(() -> runTrafficLight());
        Thread greenCar = new Thread(() -> runCars(Signal.GREEN));
        Thread redCar = new Thread(() -> runCars(Signal.RED));

        trafficLight.start();
        greenCar.start();
        redCar.start();

        greenCar.join();
        redCar.join();
        trafficLight.join();

        System.out.println("Passed: " + passedCount.get());
    }

    private static void runTrafficLight() {
        try {
            while (!stop) {
                signal = Signal.GREEN;
                Thread.sleep(GREEN_MS);
                signal = Signal.YELLOW;
                Thread.sleep(YELLOW_MS);
                signal = Signal.RED;
                Thread.sleep(RED_MS);
                signal = Signal.YELLOW;
                Thread.sleep(YELLOW_MS);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void runCars(Signal mySignal) {
        try {
            while (!stop) {
                if (signal == mySignal) {
                    go();
                    int n = passedCount.incrementAndGet();
                    if (n >= TARGET_PASSED) {
                        stop = true;
                    }
                }
                Thread.sleep(CAR_REPEAT_MS);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void go() throws InterruptedException {
        Thread.sleep(GO_DELAY_MS);
    }
}
