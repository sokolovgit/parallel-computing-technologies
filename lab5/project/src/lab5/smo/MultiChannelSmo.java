package lab5.smo;

import java.util.ArrayDeque;
import java.util.Queue;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.LockSupport;

import lab5.common.Randoms;
import lab5.common.SimulationConfig;
import lab5.common.SimulationResult;

/**
 * Simulation of an N-server queueing system with a finite buffer and rejections.
 * Each service is run as a task on a fixed {@link ExecutorService} (one thread pool worker per server).
 */
public final class MultiChannelSmo {

    /** Point-in-time view of the model for live monitoring (task 3). */
    public static final class SmoSnapshot {

        private final int queueSize;
        private final int busyChannels;
        private final long arrivalAttempts;
        private final long rejected;
        private final long served;

        public SmoSnapshot(
                int queueSize,
                int busyChannels,
                long arrivalAttempts,
                long rejected,
                long served) {
            this.queueSize = queueSize;
            this.busyChannels = busyChannels;
            this.arrivalAttempts = arrivalAttempts;
            this.rejected = rejected;
            this.served = served;
        }

        public int queueSize() {
            return queueSize;
        }

        public int busyChannels() {
            return busyChannels;
        }

        public long arrivalAttempts() {
            return arrivalAttempts;
        }

        public long rejected() {
            return rejected;
        }

        public long served() {
            return served;
        }
    }

    private final SimulationConfig cfg;
    private final Object lock = new Object();
    private final Queue<Customer> waitQueue = new ArrayDeque<>();
    private final ExecutorService channelPool;
    private final Random arrivalRng;

    private int busyChannels;
    private final AtomicLong arrivalAttempts = new AtomicLong();
    private final AtomicLong rejected = new AtomicLong();
    private final AtomicLong served = new AtomicLong();

    private final AtomicBoolean stopProducing = new AtomicBoolean();
    private final AtomicBoolean samplingActive = new AtomicBoolean(true);

    private final AtomicLong queueSampleSum = new AtomicLong();
    private final AtomicLong queueSampleCount = new AtomicLong();

    public MultiChannelSmo(SimulationConfig cfg) {
        this.cfg = cfg;
        this.channelPool = Executors.newFixedThreadPool(cfg.channels());
        this.arrivalRng = new Random(cfg.randomSeed());
    }

    /**
     * Consistent view of queue length, busy servers, and counters (for a separate status thread).
     */
    public SmoSnapshot snapshot() {
        synchronized (lock) {
            return new SmoSnapshot(
                    waitQueue.size(),
                    busyChannels,
                    arrivalAttempts.get(),
                    rejected.get(),
                    served.get());
        }
    }

    public SimulationResult run() throws InterruptedException {
        return runSimulation(0L);
    }

    /**
     * Same as {@link #run}, but a daemon {@code status-reporter} thread prints {@link #snapshot()} every
     * {@code reportIntervalMillis} (lab task 3: dynamic output in a separate thread).
     */
    public SimulationResult runWithLiveReporter(long reportIntervalMillis) throws InterruptedException {
        if (reportIntervalMillis < 1L) {
            throw new IllegalArgumentException("reportIntervalMillis must be >= 1");
        }
        return runSimulation(reportIntervalMillis);
    }

    private SimulationResult runSimulation(long reportIntervalMillis) throws InterruptedException {
        boolean withReporter = reportIntervalMillis > 0L;

        Thread sampler = new Thread(this::sampleQueueLoop, "queue-sampler");
        sampler.setDaemon(true);
        sampler.start();

        Thread producer = new Thread(this::producerLoop, "arrival-producer");
        producer.start();

        final AtomicBoolean reporterActive = new AtomicBoolean(withReporter);
        Thread reporter = null;
        if (withReporter) {
            final long period = reportIntervalMillis;
            reporter =
                    new Thread(
                            () -> {
                                // Print first, then sleep — otherwise a ~0.1 s run with a 50 ms period
                                // only shows one line (first tick was after the full sleep).
                                while (reporterActive.get()) {
                                    SmoSnapshot s = snapshot();
                                    synchronized (System.out) {
                                        System.out.printf(
                                                "[status-reporter] queue=%d busyChannels=%d "
                                                        + "arrivals=%d rejected=%d served=%d (targetServed=%d)%n",
                                                s.queueSize(),
                                                s.busyChannels(),
                                                s.arrivalAttempts(),
                                                s.rejected(),
                                                s.served(),
                                                cfg.minServed());
                                    }
                                    if (!reporterActive.get()) {
                                        break;
                                    }
                                    try {
                                        Thread.sleep(period);
                                    } catch (InterruptedException e) {
                                        Thread.currentThread().interrupt();
                                        break;
                                    }
                                }
                            },
                            "status-reporter");
            reporter.setDaemon(true);
            reporter.start();
        }

        try {
            long deadlineNanos = System.nanoTime() + TimeUnit.MINUTES.toNanos(10);
            while (served.get() < cfg.minServed()) {
                if (System.nanoTime() > deadlineNanos) {
                    stopProducing.set(true);
                    producer.join();
                    channelPool.shutdownNow();
                    samplingActive.set(false);
                    sampler.join(5_000);
                    throw new IllegalStateException(
                            "Could not reach minServed="
                                    + cfg.minServed()
                                    + " within 10 minutes; reduce load or add queue capacity / servers.");
                }
                Thread.sleep(2L);
            }
            stopProducing.set(true);
            producer.join();

            waitUntilDrained();

            channelPool.shutdown();
            boolean finished = channelPool.awaitTermination(5, TimeUnit.MINUTES);
            if (!finished) {
                channelPool.shutdownNow();
            }

            samplingActive.set(false);
            sampler.join(5_000);
        } finally {
            reporterActive.set(false);
            if (reporter != null) {
                reporter.interrupt();
                reporter.join(2_000);
            }
        }

        long samples = queueSampleCount.get();
        double meanQueue = samples == 0 ? 0.0 : queueSampleSum.get() / (double) samples;
        long attempts = arrivalAttempts.get();
        double pReject = attempts == 0 ? 0.0 : rejected.get() / (double) attempts;

        return new SimulationResult(
                meanQueue,
                pReject,
                attempts,
                rejected.get(),
                served.get(),
                samples);
    }

    /**
     * Waits until no customer is in service and the waiting buffer is empty, so no further
     * {@code execute} calls will be scheduled before {@link ExecutorService#shutdown()}.
     */
    private void waitUntilDrained() throws InterruptedException {
        long deadlineNanos = System.nanoTime() + TimeUnit.MINUTES.toNanos(5);
        while (true) {
            synchronized (lock) {
                if (waitQueue.isEmpty() && busyChannels == 0) {
                    return;
                }
            }
            if (System.nanoTime() > deadlineNanos) {
                throw new IllegalStateException(
                        "Queue/system did not drain within 5 minutes after stopping arrivals.");
            }
            Thread.sleep(1L);
        }
    }

    private void producerLoop() {
        try {
            while (!stopProducing.get()) {
                long waitNs = Randoms.nextInterArrivalNanos(arrivalRng, cfg.meanInterArrivalNanos());
                LockSupport.parkNanos(waitNs);
                admitOneArrival();
            }
        } catch (Throwable ignored) {
            // interruption or other fault — stop generating arrivals
        }
    }

    private void admitOneArrival() {
        Customer start = null;
        synchronized (lock) {
            long n = arrivalAttempts.incrementAndGet();
            if (busyChannels < cfg.channels()) {
                busyChannels++;
                start = new Customer(n);
            } else if (waitQueue.size() < cfg.queueCapacity()) {
                waitQueue.add(new Customer(n));
            } else {
                rejected.incrementAndGet();
            }
        }
        final Customer toServe = start;
        if (toServe != null) {
            channelPool.execute(() -> serveCustomer(toServe));
        }
    }

    private void serveCustomer(Customer customer) {
        long ns = Randoms.nextServiceNanos(cfg);
        LockSupport.parkNanos(ns);

        Customer next = null;
        synchronized (lock) {
            busyChannels--;
            served.incrementAndGet();
            if (!waitQueue.isEmpty()) {
                next = waitQueue.poll();
                busyChannels++;
            }
        }
        final Customer toServeNext = next;
        if (toServeNext != null) {
            channelPool.execute(() -> serveCustomer(toServeNext));
        }
    }

    private void sampleQueueLoop() {
        long intervalMs = cfg.queueSampleIntervalMillis();
        while (samplingActive.get()) {
            try {
                Thread.sleep(intervalMs);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
            int len;
            synchronized (lock) {
                len = waitQueue.size();
            }
            queueSampleSum.addAndGet(len);
            queueSampleCount.incrementAndGet();
        }
    }
}
