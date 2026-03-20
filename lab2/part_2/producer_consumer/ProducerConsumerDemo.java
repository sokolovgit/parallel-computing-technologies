package part_2.producer_consumer;

/**
 * Tests the Producer-Consumer pattern with a bounded buffer of integers.
 * Runs tests for buffer sizes 100, 1000, and 5000 and verifies correctness
 * (count, sum, no duplicates, correct sequence).
 */
public class ProducerConsumerDemo {

    /**
     * Number of integers to produce/consume per test (must be >= max buffer size).
     */
    public static final int TOTAL_ITEMS = 10_000;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Producer-Consumer (guarded blocks: wait/notifyAll)");
        System.out.println("Total items per run: " + TOTAL_ITEMS);
        System.out.println();

        runTest(100);
        runTest(1000);
        runTest(5000);
    }

    private static void runTest(int bufferSize) throws InterruptedException {
        System.out.println("Buffer size: " + bufferSize);

        BoundedBuffer buffer = new BoundedBuffer(bufferSize);
        Producer producer = new Producer(buffer, TOTAL_ITEMS);
        Consumer consumer = new Consumer(buffer, TOTAL_ITEMS);

        long start = System.nanoTime();

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();

        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        int[] received = consumer.getReceived();

        // Expected sum: 0+1+...+(TOTAL_ITEMS-1) = TOTAL_ITEMS * (TOTAL_ITEMS-1) / 2
        long expectedSum = (long) TOTAL_ITEMS * (TOTAL_ITEMS - 1) / 2;
        long actualSum = 0;
        boolean[] seen = new boolean[TOTAL_ITEMS];
        boolean orderOk = true;

        for (int i = 0; i < TOTAL_ITEMS; i++) {
            int v = received[i];
            actualSum += v;
            if (v < 0 || v >= TOTAL_ITEMS || seen[v]) {
                orderOk = false;
            } else {
                seen[v] = true;
            }
        }
        boolean noDuplicates = true;
        for (int i = 0; i < TOTAL_ITEMS; i++) {
            if (!seen[i]) {
                noDuplicates = false;
                break;
            }
        }

        boolean ok = (actualSum == expectedSum && noDuplicates && received.length == TOTAL_ITEMS && orderOk);

        System.out.println("  Count: " + received.length + " (expected " + TOTAL_ITEMS + ")");
        System.out.println("  Sum: " + actualSum + " (expected " + expectedSum + ")");
        System.out.println("  No duplicates, all 0.." + (TOTAL_ITEMS - 1) + ": " + noDuplicates);
        System.out.println("  Result: " + (ok ? "CORRECT" : "INCORRECT"));
        System.out.println("  Time: " + elapsedMs + " ms");
        System.out.println();
    }
}
