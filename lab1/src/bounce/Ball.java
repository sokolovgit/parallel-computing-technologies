package src.bounce;

import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.util.Random;

public class Ball {

    private BallCanvas canvas;

    private int x;
    private int y;
    private int dx = 2;
    private int dy = 2;

    private int size;
    private Color baseColor;

    public Ball(BallCanvas c) {
        this.canvas = c;

        updateSize();

        Random rand = new Random();

        if (Math.random() < 0.5) {
            x = rand.nextInt(Math.max(1, canvas.getWidth()));
            y = 0;
        } else {
            x = 0;
            y = rand.nextInt(Math.max(1, canvas.getHeight()));
        }

        baseColor = new Color(
                rand.nextInt(200) + 30,
                rand.nextInt(200) + 30,
                rand.nextInt(200) + 30);
    }

    private void updateSize() {
        int min = Math.min(canvas.getWidth(), canvas.getHeight());
        size = Math.max(Config.BALL_MIN_SIZE, min / 30);
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
}
