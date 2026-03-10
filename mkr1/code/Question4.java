package mkr1.code;

/**
 * Напишіть код, в якому:
 * – потік А з затримкою 100 мілісекунд переключається зі стану ”r” у стан “w” і
 * навпаки,
 * - потік В очікує стану потоку А ”r”, виводить на консоль зворотний відлік
 * мілісекунд від 1000 та призупиняє свою дію, як тільки потік А переключено у
 * стан “w”,
 * - за умови досягнення відліку мілісекунд у потоці В нульового значення обидва
 * потоки зупиняють свої дії.
 * 
 */
public class Question4 {

    static volatile boolean isAInRState = true;
    static volatile boolean running = true;

    public static void main(String[] args) throws InterruptedException {

        Thread A = new Thread(() -> {
            try {
                while (running) {
                    Thread.sleep(100);
                    isAInRState = !isAInRState;
                }
            } catch (InterruptedException ignored) {
            }
        });

        Thread B = new Thread(() -> {
            try {
                int counter = 1000;

                while (running && counter >= 0) {

                    if (isAInRState) {
                        System.out.println(counter--);
                        Thread.sleep(1);
                    } else {
                        Thread.sleep(10);
                    }
                }

                running = false;

            } catch (InterruptedException ignored) {
            }
        });

        A.start();
        B.start();

        A.join();
        B.join();
    }
}