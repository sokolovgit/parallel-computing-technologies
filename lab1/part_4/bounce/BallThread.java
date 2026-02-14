package part_4.bounce;

public class BallThread extends Thread {

    private final Ball ball;
    private final BallCanvas canvas;
    private final int maxMoves;

    public BallThread(Ball ball, BallCanvas canvas, int maxMoves) {
        this.ball = ball;
        this.canvas = canvas;
        this.maxMoves = maxMoves;
    }

    @Override
    public void run() {
        canvas.registerBallThread(this);
        try {
            for (int i = 0; i < maxMoves; i++) {
                ball.move();
                Thread.sleep(canvas.getSleepTime());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        canvas.unregisterBallThread(this);
    }
}
