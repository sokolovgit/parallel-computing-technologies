package part_4.bounce;

import javax.swing.*;
import java.awt.*;

public class BounceFrame extends JFrame {

    private final BallCanvas canvas;
    private JLabel statusLabel;

    public BounceFrame() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
        }

        setSize(Config.FRAME_WIDTH, Config.FRAME_HEIGHT);
        setTitle("Thread.join(): red → blue → green");
        setLocationRelativeTo(null);

        canvas = new BallCanvas();
        add(canvas, BorderLayout.CENTER);

        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 8));
        controlPanel.setBackground(new Color(30, 30, 30));
        controlPanel.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));

        JButton joinDemo = createButton("Red → Blue → Green (join)", new Color(80, 120, 60));
        joinDemo.addActionListener(e -> runJoinDemo());

        statusLabel = new JLabel(
                "Click the button: first the red ball moves, then the blue ball moves, then the green ball moves.");
        statusLabel.setForeground(Color.WHITE);
        statusLabel.setFont(statusLabel.getFont().deriveFont(12f));

        controlPanel.add(joinDemo);
        controlPanel.add(statusLabel);

        add(controlPanel, BorderLayout.SOUTH);
    }

    private JButton createButton(String text, Color bg) {
        JButton b = new JButton(text);
        b.setFocusPainted(false);
        b.setFont(new Font("Segoe UI", Font.BOLD, 12));
        b.setForeground(Color.WHITE);
        b.setBackground(bg);
        b.setCursor(new Cursor(Cursor.HAND_CURSOR));
        b.setBorder(BorderFactory.createEmptyBorder(8, 14, 8, 14));
        b.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                b.setBackground(brighter(bg));
            }

            public void mouseExited(java.awt.event.MouseEvent evt) {
                b.setBackground(bg);
            }
        });
        return b;
    }

    private static Color brighter(Color c) {
        return new Color(
                Math.min(255, c.getRed() + 35),
                Math.min(255, c.getGreen() + 35),
                Math.min(255, c.getBlue() + 35));
    }

    private void runJoinDemo() {
        statusLabel.setText("The red ball moves...");
        Thread worker = new Thread(() -> {
            try {
                Ball red = new Ball(canvas, Ball.BallType.RED);
                canvas.add(red);
                BallThread redThread = new BallThread(red, canvas, Config.BALL_MOVES_JOIN_DEMO);
                redThread.start();
                redThread.join();
                SwingUtilities.invokeLater(() -> statusLabel.setText("The blue ball moves..."));

                Ball blue = new Ball(canvas, Ball.BallType.BLUE);
                canvas.add(blue);
                BallThread blueThread = new BallThread(blue, canvas, Config.BALL_MOVES_JOIN_DEMO);
                blueThread.start();
                blueThread.join();
                SwingUtilities.invokeLater(() -> statusLabel.setText("The green ball moves..."));

                Ball green = new Ball(canvas, Ball.BallType.GREEN);
                canvas.add(green);
                BallThread greenThread = new BallThread(green, canvas, Config.BALL_MOVES_JOIN_DEMO);
                greenThread.start();
                greenThread.join();

                SwingUtilities.invokeLater(() -> statusLabel.setText("All three threads have finished (join)."));
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                SwingUtilities.invokeLater(() -> statusLabel.setText("Interrupted."));
            }
        });
        worker.start();
    }
}
