package part_2.producer_consumer;

/**
 * Bounded buffer of integers using the guarded block pattern (wait/notifyAll).
 * Producer blocks when buffer is full; consumer blocks when buffer is empty.
 *
 * @see <a href=
 *      "https://docs.oracle.com/javase/tutorial/essential/concurrency/guardmeth.html">Guarded
 *      Blocks</a>
 */
public class BoundedBuffer {

    private final int[] buffer;
    private final int capacity;
    private int count;
    private int putIndex;
    private int takeIndex;

    public BoundedBuffer(int capacity) {
        this.capacity = capacity;
        this.buffer = new int[capacity];
        this.count = 0;
        this.putIndex = 0;
        this.takeIndex = 0;
    }

    /**
     * Inserts the value. Blocks until the buffer is not full.
     */
    public synchronized void put(int value) throws InterruptedException {
        while (count == capacity) {
            wait();
        }

        buffer[putIndex] = value;
        putIndex = (putIndex + 1) % capacity;
        count++;

        notifyAll();
    }

    /**
     * Removes and returns the next value. Blocks until the buffer is not empty.
     */
    public synchronized int take() throws InterruptedException {
        while (count == 0) {
            wait();
        }

        int value = buffer[takeIndex];
        takeIndex = (takeIndex + 1) % capacity;
        count--;

        notifyAll();
        return value;
    }

    public int getCapacity() {
        return capacity;
    }
}
