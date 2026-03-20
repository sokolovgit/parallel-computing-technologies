package part_4.printers;

/**
 * Task 4: Three threads print '|', '\', '/'
 */
public class PrinterDemo {

    public static final int LINES = 50;
    public static final int CHARS_PER_LINE = 150;
    private static final int PRINTS_PER_THREAD = LINES * CHARS_PER_LINE / 3;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Part 4: Three threads printing | \\ /\n");
        runUncoordinated();
        runCoordinated();
    }

    private static final Object uncoordLock = new Object();
    private static int uncoordCount = 0;

    static class UncoordinatedSymbolThread extends Thread {
        private final String symbol;

        UncoordinatedSymbolThread(String symbol) {
            this.symbol = symbol;
        }

        @Override
        public void run() {
            for (int i = 0; i < PRINTS_PER_THREAD; i++) {
                synchronized (uncoordLock) {
                    System.out.print(symbol);
                    uncoordCount++;
                    if (uncoordCount % CHARS_PER_LINE == 0) {
                        System.out.println();
                    }
                }
            }
        }
    }

    private static void runUncoordinated() throws InterruptedException {
        System.out.println("Uncoordinated: " + LINES + " lines, " + CHARS_PER_LINE + " chars per line");
        uncoordCount = 0;

        Thread t1 = new UncoordinatedSymbolThread("|");
        Thread t2 = new UncoordinatedSymbolThread("\\");
        Thread t3 = new UncoordinatedSymbolThread("/");

        t1.start();
        t2.start();
        t3.start();

        t1.join();
        t2.join();
        t3.join();

        System.out.println();
    }

    private static final Object lock = new Object();
    private static int state = 0;

    static class CoordinatedSymbolThread extends Thread {
        private final String symbol;
        private final int targetState;

        CoordinatedSymbolThread(String symbol, int targetState) {
            this.symbol = symbol;
            this.targetState = targetState;
        }

        @Override
        public void run() {
            for (int i = 0; i < PRINTS_PER_THREAD; i++) {
                synchronized (lock) {
                    while (state % 3 != targetState) {
                        try {
                            lock.wait();
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                    System.out.print(symbol);
                    state++;
                    if (state % CHARS_PER_LINE == 0) {
                        System.out.println();
                    }
                    lock.notifyAll();
                }
            }
        }
    }

    private static void runCoordinated() throws InterruptedException {
        System.out.println(
                "Coordinated: " + LINES + " lines, " + CHARS_PER_LINE + " chars per line, pattern |\\/|\\/...");
        state = 0;

        Thread t1 = new CoordinatedSymbolThread("|", 0);
        Thread t2 = new CoordinatedSymbolThread("\\", 1);
        Thread t3 = new CoordinatedSymbolThread("/", 2);

        t1.start();
        t2.start();
        t3.start();
        t1.join();
        t2.join();
        t3.join();
        System.out.println();
    }
}
