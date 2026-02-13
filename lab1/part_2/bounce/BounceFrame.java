package part_2.bounce;

import javax.swing.*;
import java.awt.*;

public class BounceFrame extends JFrame {

    private BallCanvas canvas;
    private JLabel warningLabel;
    private JLabel pocketedLabel;

    public BounceFrame() {

        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
        }

        setSize(Config.FRAME_WIDTH, Config.FRAME_HEIGHT);
        setTitle("Multithreaded Billiard Simulation With Pockets");
        setLocationRelativeTo(null);

        canvas = new BallCanvas();
        add(canvas, BorderLayout.CENTER);

        pocketedLabel = new JLabel("В лузі: 0");
        pocketedLabel.setFont(new Font("Segoe UI", Font.BOLD, 14));
        pocketedLabel.setForeground(Color.WHITE);
        canvas.setPocketedLabel(pocketedLabel);

        JPanel controlPanel = new JPanel(new BorderLayout());
        controlPanel.setBackground(new Color(30, 30, 30));
        controlPanel.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));

        JPanel leftPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 5));
        leftPanel.setOpaque(false);

        JButton addOne = createButton("Add Ball");
        JButton addTen = createButton("Add 10");
        JButton exit = createButton("Exit");

        addOne.addActionListener(e -> addBall());
        addTen.addActionListener(e -> {
            for (int i = 0; i < 10; i++)
                addBall();
        });
        exit.addActionListener(e -> System.exit(0));

        leftPanel.add(addOne);
        leftPanel.add(addTen);
        leftPanel.add(exit);

        warningLabel = new JLabel("");
        warningLabel.setForeground(Color.RED);

        JPanel rightPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 15, 5));
        rightPanel.setOpaque(false);
        rightPanel.add(pocketedLabel);
        rightPanel.add(warningLabel);

        controlPanel.add(leftPanel, BorderLayout.WEST);
        controlPanel.add(rightPanel, BorderLayout.EAST);

        add(controlPanel, BorderLayout.SOUTH);
    }

    private JButton createButton(String text) {
        JButton button = new JButton(text);
        button.setFocusPainted(false);
        button.setFont(new Font("Segoe UI", Font.BOLD, 14));
        button.setForeground(Color.WHITE);
        button.setBackground(new Color(60, 120, 200));
        button.setCursor(new Cursor(Cursor.HAND_CURSOR));
        button.setBorder(BorderFactory.createEmptyBorder(8, 18, 8, 18));

        button.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                button.setBackground(new Color(80, 150, 240));
            }

            public void mouseExited(java.awt.event.MouseEvent evt) {
                button.setBackground(new Color(60, 120, 200));
            }
        });

        return button;
    }

    private void addBall() {
        Ball ball = new Ball(canvas);
        canvas.add(ball);

        BallThread thread = new BallThread(ball, canvas);
        thread.start();

        if (Thread.activeCount() > Config.WARNING_THREAD_COUNT) {
            warningLabel.setText("! High thread count!");
        } else {
            warningLabel.setText("");
        }
    }
}
