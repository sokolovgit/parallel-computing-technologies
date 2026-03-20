package part_2.producer_consumer;

/**
 * Consumes exactly totalCount integers from the buffer and stores them for verification.
 */
public class Consumer extends Thread {

    private final BoundedBuffer buffer;
    private final int totalCount;
    private final int[] received;

    public Consumer(BoundedBuffer buffer, int totalCount) {
        this.buffer = buffer;
        this.totalCount = totalCount;
        this.received = new int[totalCount];
    }

    @Override
    public void run() {
        try {
            for (int i = 0; i < totalCount; i++) {
                received[i] = buffer.take();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        }
    }

    /**
     * Returns the received values (valid only after this thread has finished).
     */
    public int[] getReceived() {
        return received;
    }
}
