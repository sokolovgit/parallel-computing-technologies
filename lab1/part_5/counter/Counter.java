package part_5.counter;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Counter {

    public enum SyncType {
        NONE,
        SYNC_METHOD,
        SYNC_BLOCK,
        LOCK
    }

    private int value;
    private final SyncType syncType;
    private final Lock lock = new ReentrantLock();

    public Counter(SyncType syncType) {
        this.syncType = syncType;
    }

    public void increment() {
        switch (syncType) {
            case NONE -> value++;
            case SYNC_METHOD -> incrementSyncMethod();
            case SYNC_BLOCK -> {
                synchronized (this) {
                    value++;
                }
            }
            case LOCK -> {
                lock.lock();
                try {
                    value++;
                } finally {
                    lock.unlock();
                }
            }
        }
    }

    public void decrement() {
        switch (syncType) {
            case NONE -> value--;
            case SYNC_METHOD -> decrementSyncMethod();
            case SYNC_BLOCK -> {
                synchronized (this) {
                    value--;
                }
            }
            case LOCK -> {
                lock.lock();
                try {
                    value--;
                } finally {
                    lock.unlock();
                }
            }
        }
    }

    private synchronized void incrementSyncMethod() {
        value++;
    }

    private synchronized void decrementSyncMethod() {
        value--;
    }

    public int getValue() {
        return value;
    }
}
