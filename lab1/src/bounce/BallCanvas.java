package src.bounce;

import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;
import java.lang.management.ManagementFactory;

public class BallCanvas extends JPanel {

    private List<Ball> balls = new ArrayList<>();
    private int sleepTime = Config.DEFAULT_SLEEP_MS;

    private long lastTime = System.nanoTime();
    private int frames = 0;
    private int fps = 0;

    private Runtime runtime = Runtime.getRuntime();

    private double processCpuLoad = 0;

    public BallCanvas() {
        setDoubleBuffered(true);
    }

    public void add(Ball b) {
        balls.add(b);
    }

    public int getBallCount() {
        return balls.size();
    }

    public void setSleepTime(int sleepTime) {
        this.sleepTime = sleepTime;
    }

    public int getSleepTime() {
        return sleepTime;
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);

        Graphics2D g2 = (Graphics2D) g;

        g2.setRenderingHint(RenderingHints.KEY_RENDERING,
                RenderingHints.VALUE_RENDER_QUALITY);
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON);

        GradientPaint table = new GradientPaint(
                0, 0, new Color(20, 90, 40),
                getWidth(), getHeight(), new Color(10, 50, 25));

        g2.setPaint(table);
        g2.fillRect(0, 0, getWidth(), getHeight());

        for (Ball b : balls) {
            b.draw(g2);
        }

        updateFPS();
        updateSystemStats();

        drawOverlay(g2);
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

        try {
            com.sun.management.OperatingSystemMXBean sunOs = (com.sun.management.OperatingSystemMXBean) ManagementFactory
                    .getOperatingSystemMXBean();

            processCpuLoad = sunOs.getProcessCpuLoad() * 100.0;

        } catch (Exception ignored) {
        }
    }

    private void drawOverlay(Graphics2D g2) {

        long usedMemory = (runtime.totalMemory() - runtime.freeMemory()) / (1024 * 1024);

        long maxMemory = runtime.maxMemory() / (1024 * 1024);

        int processors = runtime.availableProcessors();

        g2.setColor(new Color(255, 255, 255, 220));
        g2.setFont(new Font("Consolas", Font.BOLD, 14));

        int y = 20;

        g2.drawString("FPS: " + fps, 15, y);
        y += 20;
        g2.drawString("Balls: " + balls.size(), 15, y);
        y += 20;
        g2.drawString("Threads: " + Thread.activeCount(), 15, y);
        y += 20;
        g2.drawString(String.format("CPU (JVM): %.2f %%", processCpuLoad), 15, y);
        y += 20;
        g2.drawString("Used Memory: " + usedMemory + " MB", 15, y);
        y += 20;
        g2.drawString("Max Memory: " + maxMemory + " MB", 15, y);
        y += 20;
        g2.drawString("Cores: " + processors, 15, y);
    }

}
