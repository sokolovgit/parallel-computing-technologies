package part_3.bounce;

import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.Random;

public class Ball {

    public enum BallType {
        RED(Config.THREAD_PRIORITY_HIGH),
        BLUE(Config.THREAD_PRIORITY_LOW);

        private final int threadPriority;

        BallType(int threadPriority) {
            this.threadPriority = threadPriority;
        }

        public int getThreadPriority() {
            return threadPriority;
        }
    }

    private final BallCanvas canvas;

    private int x;
    private int y;
    private int dx;
    private int dy;

    private int size;
    private final Color baseColor;
    private final BallType type;

    public Ball(BallCanvas c, BallType type) {
        this.canvas = c;
        this.type = type;
        this.dx = 2;
        this.dy = 2;

        updateSize();

        Random rand = new Random();
        int w = Math.max(1, canvas.getWidth() - size);
        int h = Math.max(1, canvas.getHeight() - size);
        switch (rand.nextInt(4)) {
            case 0 -> {
                x = rand.nextInt(w);
                y = 0;
            }
            case 1 -> {
                x = rand.nextInt(w);
                y = h;
            }
            case 2 -> {
                x = 0;
                y = rand.nextInt(h);
            }
            default -> {
                x = w;
                y = rand.nextInt(h);
            }
        }

        baseColor = type == BallType.RED ? new Color(220, 50, 50) : new Color(50, 80, 200);
    }

    public Ball(BallCanvas c, int startX, int startY, int dx, int dy, BallType type) {
        this.canvas = c;
        this.type = type;
        this.x = startX;
        this.y = startY;
        this.dx = dx;
        this.dy = dy;

        updateSize();
        baseColor = type == BallType.RED ? new Color(220, 50, 50) : new Color(50, 80, 200);
    }

    private void updateSize() {
        int min = Math.min(canvas.getWidth(), canvas.getHeight());
        size = Math.max(Config.BALL_MIN_SIZE, min / 30);
    }

    public BallType getType() {
        return type;
    }

    public void draw(Graphics2D g2) {

        updateSize();

        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                RenderingHints.VALUE_ANTIALIAS_ON);

        g2.setColor(new Color(0, 0, 0, 60));
        g2.fillOval(x + 4, y + 4, size, size);

        GradientPaint gradient = new GradientPaint(
                x, y, baseColor.brighter(),
                x + size, y + size, baseColor.darker());

        g2.setPaint(gradient);
        g2.fill(new Ellipse2D.Double(x, y, size, size));

        g2.setColor(new Color(255, 255, 255, 120));
        g2.fillOval(x + size / 4, y + size / 4, size / 4, size / 4);
    }

    public void move() {

        updateSize();

        x += dx;
        y += dy;

        if (x < 0) {
            x = 0;
            dx = -dx;
        }

        if (x + size >= canvas.getWidth()) {
            x = canvas.getWidth() - size;
            dx = -dx;
        }

        if (y < 0) {
            y = 0;
            dy = -dy;
        }

        if (y + size >= canvas.getHeight()) {
            y = canvas.getHeight() - size;
            dy = -dy;
        }

        canvas.repaint();
    }

    public int getBallX() {
        return x;
    }

    public int getBallY() {
        return y;
    }

    public int getBallSize() {
        return size;
    }
}
