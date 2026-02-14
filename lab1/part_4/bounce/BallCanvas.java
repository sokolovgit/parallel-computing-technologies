package part_4.bounce;

import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

public class BallCanvas extends JPanel {

    private final List<Ball> balls = new ArrayList<>();
    private final List<BallThread> ballThreads = new ArrayList<>();
    private int sleepTime = Config.DEFAULT_SLEEP_MS;

    public BallCanvas() {
        setDoubleBuffered(true);
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

    public int getSleepTime() { return sleepTime; }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        int w = getWidth();
        int h = getHeight();
        g2.setPaint(new GradientPaint(0, 0, new Color(20, 90, 40), w, h, new Color(10, 50, 25)));
        g2.fillRect(0, 0, w, h);

        List<Ball> copy;
        synchronized (balls) {
            copy = new ArrayList<>(balls);
        }
        for (Ball b : copy)
            b.draw(g2);

        g2.setColor(Color.WHITE);
        g2.setFont(new Font("Consolas", Font.BOLD, 14));
        g2.drawString("Balls: " + balls.size() + "  Threads: " + ballThreads.size(), 15, 20);
    }
}
