package part_3.bounce;

import javax.swing.*;
import java.awt.*;

public class BounceFrame extends JFrame {

    private BallCanvas canvas;
    private JLabel warningLabel;
    private JSpinner experimentBlueCount;

    public BounceFrame() {

        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
        }

        setSize(Config.FRAME_WIDTH, Config.FRAME_HEIGHT);
        setTitle("Thread Priority: Red (high) vs Blue (low)");
        setLocationRelativeTo(null);

        canvas = new BallCanvas();
        add(canvas, BorderLayout.CENTER);

        JPanel controlPanel = new JPanel(new BorderLayout());
        controlPanel.setBackground(new Color(30, 30, 30));
        controlPanel.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));

        JPanel leftPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 5));
        leftPanel.setOpaque(false);

        JButton addRed = createButton("Add Red", new Color(180, 60, 60));
        JButton addBlue = createButton("Add Blue", new Color(60, 90, 180));
        JButton add10Blue = createButton("Add 10 Blue", new Color(60, 90, 180));
        JButton experimentBtn = createButton("Experiment: 1 Red + N Blue", new Color(100, 100, 50));
        JButton exit = createButton("Exit", new Color(80, 80, 80));

        addRed.addActionListener(e -> addBall(Ball.BallType.RED));
        addBlue.addActionListener(e -> addBall(Ball.BallType.BLUE));
        add10Blue.addActionListener(e -> {
            for (int i = 0; i < 10; i++)
                addBall(Ball.BallType.BLUE);
        });
        experimentBtn.addActionListener(e -> runExperiment());
        exit.addActionListener(e -> System.exit(0));

        experimentBlueCount = new JSpinner(new SpinnerNumberModel(15, 5, 500, 5));
        experimentBlueCount.setMaximumSize(new Dimension(70, 30));
        JLabel expLabel = new JLabel("N =");
        expLabel.setForeground(Color.WHITE);

        leftPanel.add(addRed);
        leftPanel.add(addBlue);
        leftPanel.add(add10Blue);
        leftPanel.add(expLabel);
        leftPanel.add(experimentBlueCount);

        leftPanel.add(experimentBtn);
        leftPanel.add(exit);

        warningLabel = new JLabel("");
        warningLabel.setForeground(Color.RED);

        JPanel rightPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 5));
        rightPanel.setOpaque(false);
        rightPanel.add(warningLabel);

        controlPanel.add(leftPanel, BorderLayout.WEST);
        controlPanel.add(rightPanel, BorderLayout.EAST);

        add(controlPanel, BorderLayout.SOUTH);
    }

    private JButton createButton(String text, Color bg) {
        JButton button = new JButton(text);
        button.setFocusPainted(false);
        button.setFont(new Font("Segoe UI", Font.BOLD, 12));
        button.setForeground(Color.WHITE);
        button.setBackground(bg);
        button.setCursor(new Cursor(Cursor.HAND_CURSOR));
        button.setBorder(BorderFactory.createEmptyBorder(8, 12, 8, 12));

        button.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                button.setBackground(brighter(bg));
            }

            public void mouseExited(java.awt.event.MouseEvent evt) {
                button.setBackground(bg);
            }
        });

        return button;
    }

    private static Color brighter(Color c) {
        return new Color(
                Math.min(255, c.getRed() + 40),
                Math.min(255, c.getGreen() + 40),
                Math.min(255, c.getBlue() + 40));
    }

    private void addBall(Ball.BallType type) {
        Ball ball = new Ball(canvas, type);
        canvas.add(ball);
        startBallThread(ball);
        updateWarning();
    }

    private void runExperiment() {
        int n = 20;
        try {
            Object v = experimentBlueCount.getValue();
            if (v instanceof Number)
                n = ((Number) v).intValue();
        } catch (Exception ignored) {
        }
        n = Math.max(1, Math.min(500, n));

        int w = canvas.getWidth();
        int h = canvas.getHeight();
        if (w <= 0)
            w = Config.FRAME_WIDTH;
        if (h <= 0)
            h = Config.FRAME_HEIGHT - 80;
        int size = Math.max(Config.BALL_MIN_SIZE, Math.min(w, h) / 30);
        int startX = 80;
        int startY = Math.max(0, h / 2 - size / 2);
        int dx = 2;
        int dy = 0;

        Ball redBall = new Ball(canvas, startX, startY, dx, dy, Ball.BallType.RED);
        canvas.add(redBall);

        java.util.List<Ball> blueBalls = new java.util.ArrayList<>();
        for (int i = 0; i < n; i++) {
            Ball blueBall = new Ball(canvas, startX, startY, dx, dy, Ball.BallType.BLUE);
            canvas.add(blueBall);
            blueBalls.add(blueBall);
        }

        startBallThread(redBall);
        for (Ball b : blueBalls)
            startBallThread(b);

        updateWarning();
    }

    private void startBallThread(Ball ball) {
        BallThread thread = new BallThread(ball, canvas, ball.getType().getThreadPriority());
        thread.start();
    }

    private void updateWarning() {
        if (Thread.activeCount() > Config.WARNING_THREAD_COUNT) {
            warningLabel.setText("! High thread count!");
        } else {
            warningLabel.setText("");
        }
    }
}
