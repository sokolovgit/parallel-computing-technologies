package part_5.counter;

public class CounterDemo {

    private static final int ITERATIONS = 100_000;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Counter: 2 threads, one increments 100000 times, other decrements 100000 times\n");

        runUnsafe();
        runSyncMethod();
        runSyncBlock();
        runLock();
    }

    private static void runUnsafe() throws InterruptedException {
        System.out.println("1) Unsynchronized (NONE):");
        for (int run = 1; run <= 5; run++) {
            Counter c = new Counter(Counter.SyncType.NONE);
            Thread inc = new Thread(() -> {
                for (int i = 0; i < ITERATIONS; i++)
                    c.increment();
            });
            Thread dec = new Thread(() -> {
                for (int i = 0; i < ITERATIONS; i++)
                    c.decrement();
            });
            inc.start();
            dec.start();
            inc.join();
            dec.join();
            System.out.println("   Run " + run + ": value = " + c.getValue());
        }
        System.out.println("   Expected: 0. The result is unpredictable due to the race condition.\n");
    }

    private static void runSyncMethod() throws InterruptedException {
        System.out.println("2) Synchronized method (synchronized method):");
        Counter c = new Counter(Counter.SyncType.SYNC_METHOD);
        Thread inc = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.increment();
        });
        Thread dec = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.decrement();
        });
        inc.start();
        dec.start();
        inc.join();
        dec.join();
        System.out.println("   Value = " + c.getValue() + " (correct).\n");
    }

    private static void runSyncBlock() throws InterruptedException {
        System.out.println("3) Synchronized block (synchronized block):");
        Counter c = new Counter(Counter.SyncType.SYNC_BLOCK);
        Thread inc = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.increment();
        });
        Thread dec = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.decrement();
        });
        inc.start();
        dec.start();
        inc.join();
        dec.join();
        System.out.println("   Value = " + c.getValue() + " (correct).\n");
    }

    private static void runLock() throws InterruptedException {
        System.out.println("4) Object lock (ReentrantLock):");
        Counter c = new Counter(Counter.SyncType.LOCK);
        Thread inc = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.increment();
        });
        Thread dec = new Thread(() -> {
            for (int i = 0; i < ITERATIONS; i++)
                c.decrement();
        });
        inc.start();
        dec.start();
        inc.join();
        dec.join();
        System.out.println("   Value = " + c.getValue() + " (correct).\n");
    }
}
