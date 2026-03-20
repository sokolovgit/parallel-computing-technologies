package part_2.producer_consumer;

/**
 * Produces a sequence of integers 0, 1, 2, ..., (totalCount - 1) into the buffer.
 */
public class Producer extends Thread {

    private final BoundedBuffer buffer;
    private final int totalCount;

    public Producer(BoundedBuffer buffer, int totalCount) {
        this.buffer = buffer;
        this.totalCount = totalCount;
    }

    @Override
    public void run() {
        try {
            for (int i = 0; i < totalCount; i++) {
                buffer.put(i);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        }
    }
}
