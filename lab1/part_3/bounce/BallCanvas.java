package part_3.bounce;

import javax.swing.*;
import java.awt.*;
import java.lang.Thread.State;
import java.lang.management.*;
import java.util.*;
import java.util.List;

public class BallCanvas extends JPanel {

    private final List<Ball> balls = new ArrayList<>();
    private final List<BallThread> ballThreads = new ArrayList<>();

    private int sleepTime = Config.DEFAULT_SLEEP_MS;

    private long lastTime = System.nanoTime();
    private int frames = 0;
    private int fps = 0;

    private ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();

    private com.sun.management.OperatingSystemMXBean osBean = (com.sun.management.OperatingSystemMXBean) ManagementFactory
            .getOperatingSystemMXBean();

    private double processCpuLoad = 0;
    private int runnableThreads = 0;
    private int waitingThreads = 0;
    private long totalBallCpuTime = 0;

    private LinkedList<Integer> fpsHistory = new LinkedList<>();
    private LinkedList<Double> cpuHistory = new LinkedList<>();
    private final int GRAPH_POINTS = 200;

    public BallCanvas() {
        setDoubleBuffered(true);
        threadBean.setThreadCpuTimeEnabled(true);
    }

    public void add(Ball b) {
        synchronized (balls) {
            balls.add(b);
        }
    }

    public void registerBallThread(BallThread t) {
        ballThreads.add(t);
    }

    public void unregisterBallThread(BallThread t) {
        ballThreads.remove(t);
    }

    public int getSleepTime() {
        return sleepTime;
    }

    public void setSleepTime(int sleepTime) {
        this.sleepTime = sleepTime;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;

        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON);

        drawBackground(g2);

        List<Ball> copy;
        synchronized (balls) {
            copy = new ArrayList<>(balls);
        }

        for (Ball b : copy) {
            if (b.getType() == Ball.BallType.BLUE)
                b.draw(g2);
        }
        for (Ball b : copy) {
            if (b.getType() == Ball.BallType.RED)
                b.draw(g2);
        }

        updateFPS();
        updateSystemStats();
        updateThreadStats();
        updateCpuTime();
        updateGraph();

        drawOverlay(g2);
        drawGraph(g2);
    }

    private void drawBackground(Graphics2D g2) {
        int w = getWidth();
        int h = getHeight();
        GradientPaint table = new GradientPaint(
                0, 0, new Color(20, 90, 40),
                w, h, new Color(10, 50, 25));
        g2.setPaint(table);
        g2.fillRect(0, 0, w, h);
    }

    private void updateFPS() {
        frames++;
        long current = System.nanoTime();

        if (current - lastTime >= 1_000_000_000) {
            fps = frames;
            frames = 0;
            lastTime = current;
        }
    }

    private void updateSystemStats() {
        processCpuLoad = osBean.getProcessCpuLoad() * 100.0;
    }

    private void updateThreadStats() {

        runnableThreads = 0;
        waitingThreads = 0;

        for (BallThread t : ballThreads) {
            State state = t.getState();

            switch (state) {
                case RUNNABLE -> runnableThreads++;
                case WAITING, TIMED_WAITING -> waitingThreads++;
                case BLOCKED, NEW, TERMINATED -> {
                }
            }
        }
    }

    private void updateCpuTime() {
        totalBallCpuTime = 0;

        for (BallThread t : ballThreads) {
            long id = t.threadId();
            totalBallCpuTime += threadBean.getThreadCpuTime(id);
        }
    }

    private void updateGraph() {
        fpsHistory.add(fps);
        cpuHistory.add(processCpuLoad);

        if (fpsHistory.size() > GRAPH_POINTS)
            fpsHistory.removeFirst();
        if (cpuHistory.size() > GRAPH_POINTS)
            cpuHistory.removeFirst();
    }

    private void drawOverlay(Graphics2D g2) {

        double frameTime = fps > 0 ? 1000.0 / fps : 0;

        g2.setColor(Color.WHITE);
        g2.setFont(new Font("Consolas", Font.BOLD, 14));

        int y = 20;

        g2.drawString("Balls: " + balls.size(), 15, y);
        y += 20;
        g2.drawString("Ball Threads: " + ballThreads.size(), 15, y);
        y += 20;
        g2.drawString("FPS: " + fps, 15, y);
        y += 20;
        g2.drawString(String.format("Frame Time: %.2f ms", frameTime), 15, y);
        y += 20;
        g2.drawString(String.format("CPU (JVM): %.2f %%", processCpuLoad), 15, y);
        y += 20;
        g2.drawString("RUNNABLE: " + runnableThreads, 15, y);
        y += 20;
        g2.drawString("WAITING: " + waitingThreads, 15, y);
        y += 20;
        g2.drawString("Ball CPU Time (ms): " + totalBallCpuTime / 1_000_000, 15, y);
    }

    private void drawGraph(Graphics2D g2) {

        int width = 300;
        int height = 150;

        int x = getWidth() - width - 20;
        int y = 20;

        g2.setColor(new Color(0, 0, 0, 120));
        g2.fillRect(x, y, width, height);

        g2.setColor(Color.GREEN);
        drawLineGraph(g2, fpsHistory, x, y, width, height, 100);

        g2.setColor(Color.RED);
        drawLineGraphDouble(g2, cpuHistory, x, y, width, height, 100);
    }

    private void drawLineGraph(Graphics2D g2, List<Integer> data,
            int x, int y, int width, int height, int maxValue) {

        if (data.size() < 2)
            return;

        int step = width / GRAPH_POINTS;
        int prevX = x;
        int prevY = y + height - (data.get(0) * height / maxValue);

        for (int i = 1; i < data.size(); i++) {
            int currentX = x + i * step;
            int currentY = y + height - (data.get(i) * height / maxValue);

            g2.drawLine(prevX, prevY, currentX, currentY);

            prevX = currentX;
            prevY = currentY;
        }
    }

    private void drawLineGraphDouble(Graphics2D g2, List<Double> data,
            int x, int y, int width, int height, int maxValue) {

        if (data.size() < 2)
            return;

        int step = width / GRAPH_POINTS;
        int prevX = x;
        int prevY = y + height - ((int) (data.get(0) * height / maxValue));

        for (int i = 1; i < data.size(); i++) {
            int currentX = x + i * step;
            int currentY = y + height - ((int) (data.get(i) * height / maxValue));

            g2.drawLine(prevX, prevY, currentX, currentY);

            prevX = currentX;
            prevY = currentY;
        }
    }
}
