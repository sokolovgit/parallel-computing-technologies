package part_1.bank;

/**
 * Asynchronous bank test based on the listing from the lab assignment.
 * Contains one unsafe implementation and three different synchronized variants.
 */
public class AsynchBankTest {

    public static final int NACCOUNTS = 10;
    public static final int INITIAL_BALANCE = 10_000;
    /**
     * How many transfer operations each thread performs.
     */
    public static final int REPS = 100_000;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("AsynchBankTest: " + NACCOUNTS + " accounts, initial balance " + INITIAL_BALANCE);
        System.out.println("Total expected sum: " + (NACCOUNTS * INITIAL_BALANCE));

        runVariantUnsafe();
        runVariantSynchronized();
        runVariantLock();
        runVariantAtomic();
    }

    private static void runVariantUnsafe() throws InterruptedException {
        System.out.println();
        System.out.println("1) UNSAFE variant (no synchronization, race condition):");
        System.out
                .println("   (Run multiple times to see sum often diverge from " + (NACCOUNTS * INITIAL_BALANCE) + ")");

        for (int run = 1; run <= 3; run++) {
            System.out.println("   Run " + run + ":");
            Bank bank = new UnsafeBank(NACCOUNTS, INITIAL_BALANCE);
            startAndJoinAllThreads(bank);
            System.out.println();
        }
    }

    private static void runVariantSynchronized() throws InterruptedException {
        System.out.println();
        System.out.println("2) SYNCHRONIZED methods variant:");
        Bank bank = new SynchronizedBank(NACCOUNTS, INITIAL_BALANCE);
        startAndJoinAllThreads(bank);
        System.out.println();
    }

    private static void runVariantLock() throws InterruptedException {
        System.out.println();
        System.out.println("3) ReentrantLock variant:");
        Bank bank = new LockBank(NACCOUNTS, INITIAL_BALANCE);
        startAndJoinAllThreads(bank);
        System.out.println();
    }

    private static void runVariantAtomic() throws InterruptedException {
        System.out.println();
        System.out.println("4) AtomicIntegerArray + AtomicLong variant:");
        Bank bank = new AtomicBank(NACCOUNTS, INITIAL_BALANCE);
        startAndJoinAllThreads(bank);
        System.out.println();
    }

    private static void startAndJoinAllThreads(Bank bank) throws InterruptedException {
        TransferThread[] threads = new TransferThread[NACCOUNTS];
        for (int i = 0; i < NACCOUNTS; i++) {
            threads[i] = new TransferThread(bank, i, INITIAL_BALANCE, REPS);
            threads[i].setPriority(Thread.NORM_PRIORITY + i % 2);
            threads[i].start();
        }
        for (TransferThread t : threads) {
            t.join();
        }

        // final consistency check
        if (bank instanceof TestableBank testableBank) {
            testableBank.test();
        }
    }
}
