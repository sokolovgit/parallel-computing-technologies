package part_1.bank;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.util.concurrent.atomic.AtomicLong;

interface Bank {
    void transfer(int from, int to, int amount);

    int size();
}

interface TestableBank {
    void test();
}

abstract class AbstractBank implements Bank, TestableBank {

    protected static final int NTEST = 10_000;

    protected final int[] accounts;
    protected long ntransacts = 0;

    protected AbstractBank(int n, int initialBalance) {
        accounts = new int[n];
        for (int i = 0; i < accounts.length; i++) {
            accounts[i] = initialBalance;
        }
    }

    protected void doTransfer(int from, int to, int amount) {
        if (from == to) {
            return;
        }
        if (amount <= 0) {
            return;
        }

        if (accounts[from] < amount) {
            return;
        }

        accounts[from] -= amount;
        accounts[to] += amount;
        ntransacts++;
        if (ntransacts % NTEST == 0) {
            test();
        }
    }

    @Override
    public int size() {
        return accounts.length;
    }

    @Override
    public void test() {
        int sum = 0;
        for (int account : accounts) {
            sum += account;
        }
        System.out.println(
                getClass().getSimpleName()
                        + " -> transactions: " + ntransacts
                        + ", sum: " + sum);
    }
}

/**
 * Completely unsafe bank: no synchronization at all.
 * This version demonstrates race conditions and incorrect sums.
 */
class UnsafeBank extends AbstractBank {

    UnsafeBank(int n, int initialBalance) {
        super(n, initialBalance);
    }

    @Override
    public void transfer(int from, int to, int amount) {
        doTransfer(from, to, amount);
    }
}

/**
 * Bank using synchronized methods (implicit monitor on this).
 */
class SynchronizedBank extends AbstractBank {

    SynchronizedBank(int n, int initialBalance) {
        super(n, initialBalance);
    }

    @Override
    public synchronized void transfer(int from, int to, int amount) {
        doTransfer(from, to, amount);
    }

    @Override
    public synchronized void test() {
        super.test();
    }
}

/**
 * Bank using an explicit ReentrantLock as a single global lock.
 */
class LockBank extends AbstractBank {

    private final Lock lock = new ReentrantLock();

    LockBank(int n, int initialBalance) {
        super(n, initialBalance);
    }

    @Override
    public void transfer(int from, int to, int amount) {
        lock.lock();
        try {
            doTransfer(from, to, amount);
        } finally {
            lock.unlock();
        }
    }

    @Override
    public void test() {
        lock.lock();
        try {
            super.test();
        } finally {
            lock.unlock();
        }
    }
}

/**
 * Bank that stores balances in AtomicIntegerArray and uses AtomicLong
 * for the transaction counter. All modifications and tests are still
 * protected by a ReentrantLock to keep the global invariant (constant sum).
 */
class AtomicBank implements Bank, TestableBank {

    private static final int NTEST = 10_000;

    private final AtomicIntegerArray accounts;
    private final AtomicLong ntransacts = new AtomicLong(0);
    private final int expectedTotal;
    private final Lock lock = new ReentrantLock();

    AtomicBank(int n, int initialBalance) {
        accounts = new AtomicIntegerArray(n);
        for (int i = 0; i < n; i++) {
            accounts.set(i, initialBalance);
        }
        expectedTotal = n * initialBalance;
    }

    @Override
    public void transfer(int from, int to, int amount) {
        if (from == to || amount <= 0) {
            return;
        }

        lock.lock();
        try {
            int fromBalance = accounts.get(from);
            if (fromBalance < amount) {
                return;
            }
            accounts.addAndGet(from, -amount);
            accounts.addAndGet(to, amount);
            long t = ntransacts.incrementAndGet();
            if (t % NTEST == 0) {
                test();
            }
        } finally {
            lock.unlock();
        }
    }

    @Override
    public int size() {
        return accounts.length();
    }

    @Override
    public void test() {
        lock.lock();
        try {
            int sum = 0;
            for (int i = 0; i < accounts.length(); i++) {
                sum += accounts.get(i);
            }
            System.out.println(
                    getClass().getSimpleName()
                            + " -> transactions: " + ntransacts.get()
                            + ", sum: " + sum
                            + ", expected: " + expectedTotal);
        } finally {
            lock.unlock();
        }
    }
}

